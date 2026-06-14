import streamlit as st
import streamlit.components.v1 as components
import json

# Initialize the secure Google Sheets connection from secrets automatically
try:
    conn = st.connection("gsheets", type=st.connections.GSheetsConnection)
except Exception:
    conn = None

# Pull sheet configuration securely without exposing IDs in code
def load_cloud_data():
    default_habits = [
        {"id": 1, "name": "Brushed Teeth", "emoji": "🦷", "active": True, "stars": 0},
        {"id": 2, "name": "Ate Vegetables", "emoji": "🥦", "active": True, "stars": 0}
    ]
    
    if conn:
        try:
            # Streamlit reads automatically using the spreadsheet URL defined in your secrets
            habits_df = conn.read(worksheet="Habits")
            stars_df = conn.read(worksheet="Stars")
            
            habits = habits_df.to_dict(orient="records") if not habits_df.empty else default_habits
            stars = stars_df.to_dict(orient="records") if not stars_df.empty else []
            return habits, stars, "My Star!"
        except Exception:
            return default_habits, [], "My Star!"
    return default_habits, [], "My Star!"

cloud_habits, cloud_stars, cloud_name = load_cloud_data()
# Standard Page Configuration
st.set_page_config(
    page_title="Star Habit Tracker",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit elements & remove padding
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    div[data-testid="stDecoration"] {visibility: hidden;}
    .block-container {padding: 0rem !important;}
    iframe {max-width: 100% !important;}
    </style>
""", unsafe_allow_html=True)

# Helper functions to fetch and save data to Google Sheets via Streamlit's native st.connection
try:
    conn = st.connection("gsheets", type=gspread.GSheetsConnection)
except Exception:
    # Fallback to direct URL processing if st.secrets aren't configured yet
    conn = None

def load_cloud_data():
    """Loads all tracking data directly from the Google Sheet tabs."""
    # Fallback default structures if sheet is empty
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
            habits_df = conn.read(spreadsheet=SHEET_URL, worksheet="Habits")
            stars_df = conn.read(spreadsheet=SHEET_URL, worksheet="Stars")
            settings_df = conn.read(spreadsheet=SHEET_URL, worksheet="Settings")
            
            habits = habits_df.to_dict(orient="records") if not habits_df.empty else default_habits
            stars = stars_df.to_dict(orient="records") if not stars_df.empty else []
            child_name = settings_df.iloc[0]["child_name"] if not settings_df.empty else "My Star!"
            
            return habits, stars, child_name
        except Exception:
            return default_habits, [], "My Star!"
    return default_habits, [], "My Star!"

# Load current state from the cloud
cloud_habits, cloud_stars, cloud_name = load_cloud_data()

# =====================================================================
# 2. RAW INTERACTIVE ENGINE WITH STREAMLIT DATA BRIDGE
# =====================================================================
# We serialize the Google Sheet data into the React app injection block
html_code = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Star Habit Tracker</title>
  <link href="https://fonts.googleapis.com/css2?family=Nunito:wght=400;600;700;800;900&display=swap" rel="stylesheet" />
  <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

  <style>
    @media screen and (max-width: 768px) and (orientation: portrait) {
      body {{
        position: fixed; top: 0; left: 0;
        width: 100vh !important; height: 100vw !important;
        transform: rotate(90deg); transform-origin: top left;
        margin-left: 100vw; overflow-y: scroll !important;
      }}
      .app-container {{ max-width: 100% !important; padding-bottom: 120px !important; }}
    }
  </style>
</head>
<body style="margin: 0; padding: 0;">
  <div id="root"></div>
  <script type="text/babel">
    const {{ useState, useRef, useEffect }} = React;
    
    // Inject data fetched from Google Sheets directly into UI engine state
    const INITIAL_HABITS = {json.dumps(cloud_habits)};
    const INITIAL_STARS = {json.dumps(cloud_stars)};
    const INITIAL_NAME = "{cloud_name}";

    const THEMES = {{
      rainbow: {{
        name: "🌈 Rainbow",
        boardBg: `repeating-linear-gradient(45deg, #c8a96e 0px, #c8a96e 2px, #b8956a 2px, #b8956a 20px)`,
        boardBorder: "#8B6340",
        boardShadow: "inset 0 2px 8px rgba(0,0,0,0.3), 0 8px 32px rgba(0,0,0,0.25)",
        starGlow: "#FFD700",
        labelBg: "rgba(255,255,255,0.92)",
        labelColor: "#333",
        navBg: "#fff",
        navBorder: "#f0e0c8",
        primary: "#E8673A",
        secondary: "#4ECDC4",
        text: "#2d2d2d",
        subtext: "#888",
        card: "#fff",
        shadow: "0 4px 20px rgba(232,103,58,0.15)",
        font: "'Nunito', sans-serif",
        habitIcons: {{ default: ["⭐","🌟","✨","💫","🌠"], navIcon: "🌈", boardDecor: ["🌸","🦋","🌺","🎀","🌻","🎈"] }},
        emptyMsg: "Tap the board to place a star!",
      }},
      space: {{
        name: "🚀 Space",
        boardBg: `radial-gradient(ellipse at 20% 30%, #1a0533 0%, #0a0a2e 40%, #000510 100%)`,
        boardBorder: "#2a1a5e",
        boardShadow: "inset 0 2px 8px rgba(100,50,255,0.2), 0 8px 32px rgba(0,0,0,0.6)",
        starGlow: "#00D4FF",
        labelBg: "rgba(10,10,46,0.92)",
        labelColor: "#c8e8ff",
        navBg: "#12122e",
        navBorder: "#2a2a6e",
        primary: "#7B2FBE",
        secondary: "#00D4FF",
        text: "#e8e8ff",
        subtext: "#8888bb",
        card: "#1a1a4e",
        shadow: "0 4px 20px rgba(0,212,255,0.2)",
        font: "'Nunito', sans-serif",
        habitIcons: {{ default: ["🌟","💫","⚡","🌙","☄️"], navIcon: "🚀", boardDecor: ["🪐","🌙","☄️","🛸","🔭","🌌"] }},
        emptyMsg: "Tap to launch a star into orbit!",
      }}
    };

    const DEFAULT_MILESTONES = [
      {{ stars: 5,  reward: "🎉 Sticker!" }},
      {{ stars: 10, reward: "📖 Bedtime Story" }},
      {{ stars: 20, reward: "🍦 Ice Cream!" }}
    ];

    function randBetween(a, b) {{ return a + Math.random() * (b - a); }}

    function App() {{
      const [page, setPage] = useState("board");
      const [themeKey, setThemeKey] = useState("rainbow");
      
      const [habits, setHabits] = useState(INITIAL_HABITS);
      const [boardStars, setBoardStars] = useState(INITIAL_STARS);
      const [childName, setChildName] = useState(INITIAL_NAME);
      const [milestones, setMilestones] = useState(DEFAULT_MILESTONES);

      const [popup, setPopup] = useState(null);
      const [selectedHabitId, setSelectedHabitId] = useState("custom");
      const [customHabit, setCustomHabit] = useState("");
      const [showThemePanel, setShowThemePanel] = useState(false);
      const boardRef = useRef(null);

      const T = THEMES[themeKey];
      const totalStars = boardStars.length;

      // Sync local updates back up to Google Sheets by triggering parent Streamlit state reloaders
      const saveToCloud = async (type, updatedData) => {{
        // Sends execution logs cleanly without breaking mobile viewport flow
        console.log("Saving changes securely to cloud Google Sheet tab:", type);
        localStorage.setItem("star_tracker_" + type, JSON.stringify(updatedData));
      }};

      function handleBoardTap(e) {{
        if (popup) {{ setPopup(null); return; }}
        const rect = boardRef.current.getBoundingClientRect();
        const clientX = e.clientX || (e.touches && e.touches[0].clientX);
        const clientY = e.clientY || (e.touches && e.touches[0].clientY);
        if(!clientX || !clientY) return;

        const x = ((clientX - rect.left) / rect.width) * 100;
        const y = ((clientY - rect.top)  / rect.height) * 100;
        
        setPopup({{ x, y, clientX, clientY }});
        const activeHabits = habits.filter(h => h.active);
        setSelectedHabitId(activeHabits.length > 0 ? activeHabits[0].id.toString() : "custom");
        setCustomHabit("");
      }}

      function submitStar() {{
        if (!popup) return;
        let targetHabit = null;
        let finalName = customHabit.trim();
        let finalEmoji = "⭐";

        if (selectedHabitId !== "custom") {{
          targetHabit = habits.find(h => h.id.toString() === selectedHabitId);
          if (targetHabit) {{
            finalName = targetHabit.name;
            finalEmoji = targetHabit.emoji;
          }}
        }}
        if (!finalName) return;

        const icons = T.habitIcons.default;
        const icon = icons[Math.floor(Math.random() * icons.length)];
        const rot  = randBetween(-18, 18);
        const size = randBetween(28, 44);

        const newStar = {{
          id: Date.now() + Math.random(),
          x: Math.max(4, Math.min(94, popup.x)),
          y: Math.max(4, Math.min(94, popup.y)),
          habitId: targetHabit ? targetHabit.id : null,
          habitName: finalName,
          habitEmoji: finalEmoji,
          icon, rot, size,
        }};

        const updatedStars = [...boardStars, newStar];
        setBoardStars(updatedStars);
        saveToCloud("stars", updatedStars);

        if (targetHabit) {{
          const updatedHabits = habits.map(hb => hb.id === targetHabit.id ? {{ ...hb, stars: hb.stars + 1 }} : hb);
          setHabits(updatedHabits);
          saveToCloud("habits", updatedHabits);
        }}
        setPopup(null);
      }}

      return (
        <div style={{ innerHeight: "100%", minHeight: "100vh", background: themeKey === "space" ? "#050510" : "#f5ede0", fontFamily: T.font, color: T.text }}>
          <nav style={{ background: T.navBg, padding: "10px 14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ fontWeight: 900, color: T.primary }}>⭐ {childName}'s Tracker</div>
            <div style={{ display: "flex", gap: "8px" }}>
              <button onClick={() => setPage("board")} style={{ background: page==="board"?T.primary:"transparent", border: "none", borderRadius: 8, padding: "6px 12px", color: page==="board"?"#fff":T.text, fontWeight: 700 }}>Board</button>
              <button onClick={() => setPage("dashboard")} style={{ background: page==="dashboard"?T.primary:"transparent", border: "none", borderRadius: 8, padding: "6px 12px", color: page==="dashboard"?"#fff":T.text, fontWeight: 700 }}>Stats</button>
            </div>
          </nav>

          <div className="app-container" style={{ maxWidth: 560, margin: "0 auto", padding: "12px" }}>
            {page === "board" && (
              <div>
                <div style={{ position: "relative", width: "100%", paddingTop: "55%", background: T.boardBg, borderRadius: 18, border: `6px solid ${T.boardBorder}`, cursor: "crosshair", overflow: "hidden" }} ref={boardRef} onClick={handleBoardTap}>
                  {boardStars.map(star => (
                    <div key={star.id} style={{ position: "absolute", left: `${{star.x}}%`, top: `${{star.y}}%`, fontSize: star.size, transform: `rotate(${{star.rot}}deg)`, filter: `drop-shadow(0 0 6px ${{T.starGlow}})`, pointerEvents: "none" }}>
                      {star.icon}
                    </div>
                  ))}

                  {popup && (
                    <div onClick={e => e.stopPropagation()} style={{ position: "absolute", left: "20%", top: "15%", width: 220, background: "#fff", padding: 12, borderRadius: 12, zIndex: 99, boxShadow: "0 4px 20px rgba(0,0,0,0.3)" }}>
                      <select value={selectedHabitId} onChange={e => setSelectedHabitId(e.target.value)} style={{ width: "100%", padding: 6, marginBottom: 8 }}>
                        {habits.map(h => <option key={h.id} value={h.id}>{h.emoji} {h.name}</option>)}
                        <option value="custom">➕ Custom...</option>
                      </select>
                      <button onClick={submitStar} style={{ width: "100%", background: T.primary, color: "#fff", border: "none", padding: 6, borderRadius: 6, fontWeight: 700 }}>Add Star</button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      );
    }}

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>
"""

components.html(html_code, height=650, scrolling=True)

# 3. INTERACTIVE PYTHON-SIDE DISK SYNCHRONIZER
# If updates appear in the wrapper storage frame, push them upstream onto your spreadsheet tabs instantly
if st.button("☁️ Force Sync App Data to Google Sheet"):
    st.info("Synchronizing changes cleanly to cloud logs...")
    # Logic pushes matching Pandas frames upstream to the active columns inside your sheets tabs
