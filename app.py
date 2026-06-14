import streamlit as st
import streamlit.components.v1 as components
import json
import pandas as pd
import os
import hashlib

# 1. Page Config
st.set_page_config(
    page_title="Star Habit Tracker",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    div[data-testid="stDecoration"] {visibility: hidden;}
    .block-container {padding: 0rem !important;}
    iframe {max-width: 100% !important; border: none !important;}
    </style>
""", unsafe_allow_html=True)

# 2. Connection & Data Load
try:
    conn = st.connection("gsheets", type=st.connections.GSheetsConnection)
except Exception:
    conn = None

def load_cloud_data():
    default_habits = [
        {"id": 1, "name": "Brushed Teeth", "emoji": "🦷", "active": True, "stars": 0},
        {"id": 2, "name": "Ate Vegetables", "emoji": "🥦", "active": True, "stars": 0},
        {"id": 3, "name": "Said Please & Thank You", "emoji": "🙏", "active": True, "stars": 0},
        {"id": 4, "name": "Slept on Time", "emoji": "😴", "active": True, "stars": 0},
        {"id": 5, "name": "Cleaned Up Toys", "emoji": "🧸", "active": True, "stars": 0},
        {"id": 6, "name": "Washed Hands", "emoji": "🤲", "active": True, "stars": 0}
    ]
    if conn:
        try:
            habits_df = conn.read(worksheet="Habits")
            habits = habits_df.to_dict(orient="records") if not habits_df.empty else default_habits
            stars_df = conn.read(worksheet="Stars")
            stars = stars_df.to_dict(orient="records") if not stars_df.empty else []
            settings_df = conn.read(worksheet="Settings")
            child_name = settings_df.iloc[0]["child_name"] if not settings_df.empty else "My Star!"
            return habits, stars, child_name
        except: pass
    return default_habits, [], "My Star!"

if "habits_data" not in st.session_state:
    st.session_state["habits_data"], st.session_state["stars_data"], st.session_state["child_name"] = load_cloud_data()

# 3. Frontend Generator
html_code = """
<!DOCTYPE html>
<html>
<head>
  <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    const { useState, useEffect } = React;
    const INITIAL_HABITS = INITIAL_HABITS_PLACEHOLDER;
    const INITIAL_STARS = INITIAL_STARS_PLACEHOLDER;
    const INITIAL_NAME = INITIAL_NAME_PLACEHOLDER;

    function App() {
      const [stars, setStars] = useState(INITIAL_STARS);
      const [habits, setHabits] = useState(INITIAL_HABITS);
      const [name, setName] = useState(INITIAL_NAME);

      useEffect(() => {
        window.parent.postMessage({ type: "streamlit:componentReady" }, "*");
      }, []);

      const sendToPython = (s, h, n) => {
        window.parent.postMessage({
          isStreamlitMessage: true,
          type: "streamlit:setComponentValue",
          value: { stars: s, habits: h, child_name: n }
        }, "*");
      };

      // Add your UI logic here
      return <div onClick={() => {
        const newStar = { id: Date.now() };
        const updatedStars = [...stars, newStar];
        setStars(updatedStars);
        sendToPython(updatedStars, habits, name);
      }}>Click to Add Star ({stars.length})</div>;
    }
    ReactDOM.createRoot(document.getElementById('root')).render(<App />);
  </script>
</body>
</html>
"""

# 4. Optimized I/O Throttled Write
PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
COMPONENT_DIR = os.path.join(PARENT_DIR, "tracker_frontend")
if not os.path.exists(COMPONENT_DIR): os.makedirs(COMPONENT_DIR)

html_final = html_code.replace("INITIAL_HABITS_PLACEHOLDER", json.dumps(st.session_state["habits_data"])) \
                      .replace("INITIAL_STARS_PLACEHOLDER", json.dumps(st.session_state["stars_data"])) \
                      .replace("INITIAL_NAME_PLACEHOLDER", json.dumps(st.session_state["child_name"]))

html_path = os.path.join(COMPONENT_DIR, "index.html")
# Only write if file doesn't exist to prevent reset loops
if not os.path.exists(html_path):
    with open(html_path, "w", encoding="utf-8") as f: f.write(html_final)

# 5. Component Logic
tracker_comp = components.declare_component("tracker", path=COMPONENT_DIR)
val = tracker_comp(key="main_tracker")

if val:
    new_state = {"stars": val.get("stars"), "habits": val.get("habits"), "name": val.get("child_name")}
    state_hash = hashlib.md5(str(new_state).encode()).hexdigest()
    
    if state_hash != st.session_state.get("last_hash"):
        st.session_state["last_hash"] = state_hash
        st.session_state["habits_data"] = val.get("habits")
        st.session_state["stars_data"] = val.get("stars")
        
        if conn:
            conn.update(worksheet="Habits", data=pd.DataFrame(val.get("habits")))
            conn.update(worksheet="Stars", data=pd.DataFrame(val.get("stars")))
        st.rerun()
        
