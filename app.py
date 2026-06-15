import streamlit as st
import streamlit.components.v1 as components
import json
import pandas as pd
import os
import hashlib

# ─── 1. PAGE CONFIG ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Star Habit Tracker",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    div[data-testid="stDecoration"] {visibility: hidden;}
    .block-container {padding: 0rem !important;}
    iframe {max-width: 100% !important; border: none !important;}
    </style>
""", unsafe_allow_html=True)

# ─── 2. GOOGLE SHEETS CONNECTION ───────────────────────────────────────────
conn = None
try:
    from streamlit_gsheets import GSheetsConnection
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    conn = None

DEFAULT_HABITS = [
    {"id": 1, "name": "Brushed Teeth",          "emoji": "🦷", "active": True, "stars": 0},
    {"id": 2, "name": "Ate Vegetables",          "emoji": "🥦", "active": True, "stars": 0},
    {"id": 3, "name": "Said Please & Thank You", "emoji": "🙏", "active": True, "stars": 0},
    {"id": 4, "name": "Slept on Time",           "emoji": "😴", "active": True, "stars": 0},
    {"id": 5, "name": "Cleaned Up Toys",         "emoji": "🧸", "active": True, "stars": 0},
    {"id": 6, "name": "Washed Hands",            "emoji": "🤲", "active": True, "stars": 0},
]

def load_cloud_data():
    if conn:
        try:
            habits_df = conn.read(worksheet="Habits", ttl=0)
            habits = habits_df.to_dict(orient="records") if not habits_df.empty else DEFAULT_HABITS
            for h in habits:
                h["active"] = bool(h.get("active", True))
                h["stars"]  = int(h.get("stars", 0))

            stars_df = conn.read(worksheet="Stars", ttl=0)
            stars = stars_df.to_dict(orient="records") if not stars_df.empty else []

            settings_df = conn.read(worksheet="Settings", ttl=0)
            child_name  = str(settings_df.iloc[0]["child_name"]) if not settings_df.empty else "My Star!"

            theme_key = "rainbow"
            if not settings_df.empty and "theme_key" in settings_df.columns:
                theme_key = str(settings_df.iloc[0].get("theme_key", "rainbow"))

            return habits, stars, child_name, theme_key
        except Exception as e:
            st.warning(f"Could not load from Google Sheets: {e}. Using local defaults.")

    return DEFAULT_HABITS, [], "My Star!", "rainbow"

def save_cloud_data(habits, stars, child_name, theme_key):
    if not conn:
        return
    try:
        conn.update(worksheet="Habits", data=pd.DataFrame(habits))
        if stars:
            conn.update(worksheet="Stars", data=pd.DataFrame(stars))
        else:
            conn.update(worksheet="Stars", data=pd.DataFrame(
                columns=["id", "x", "y", "habitName", "habitEmoji", "icon", "rot", "size"]
            ))
        conn.update(worksheet="Settings", data=pd.DataFrame(
            [{"child_name": child_name, "theme_key": theme_key}]
        ))
    except Exception as e:
        st.warning(f"Could not save to Google Sheets: {e}")

# ─── 3. SESSION STATE INIT ─────────────────────────────────────────────────
if "initialized" not in st.session_state:
    habits, stars, child_name, theme_key = load_cloud_data()
    st.session_state["habits_data"] = habits
    st.session_state["stars_data"]  = stars
    st.session_state["child_name"]  = child_name
    st.session_state["theme_key"]   = theme_key
    st.session_state["last_hash"]   = ""
    st.session_state["initialized"] = True

# ─── 4. BUILD FRONTEND HTML ────────────────────────────────────────────────
def build_html(habits, stars, child_name, theme_key):
    habits_json     = json.dumps(habits,     ensure_ascii=False)
    stars_json      = json.dumps(stars,      ensure_ascii=False)
    child_name_json = json.dumps(child_name, ensure_ascii=False)
    theme_key_json  = json.dumps(theme_key,  ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Star Habit Tracker</title>
  <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap" rel="stylesheet" />
  <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Nunito', sans-serif; overflow-x: hidden; }}
    @keyframes floatIn {{
      0%   {{ transform: scale(0) rotate(var(--rot)) translateY(8px); opacity:0; }}
      60%  {{ transform: scale(1.35) rotate(var(--rot)) translateY(-4px); opacity:1; }}
      100% {{ transform: scale(1) rotate(var(--rot)) translateY(0); opacity:1; }}
    }}
    @keyframes starPulse {{
      0%,100% {{ filter: drop-shadow(0 0 6px var(--glow)) drop-shadow(0 0 14px var(--glow2)); }}
      50%      {{ filter: drop-shadow(0 0 10px var(--glow)) drop-shadow(0 0 22px var(--glow2)) brightness(1.3); }}
    }}
    @keyframes boardDecorFloat {{
      0%,100% {{ transform:translateY(0); }}
      50%      {{ transform:translateY(-5px); }}
    }}
    @keyframes toastIn {{
      from {{ transform: translate(-50%,-50%) scale(0.4); opacity:0; }}
      to   {{ transform: translate(-50%,-50%) scale(1);   opacity:1; }}
    }}
    .board-star {{
      position:absolute; user-select:none; pointer-events:none;
      animation: floatIn 0.45s cubic-bezier(.34,1.56,.64,1) forwards,
                 starPulse 2.8s ease-in-out infinite 0.5s;
    }}
    .habit-pill {{
      display:flex; align-items:center; gap:10px;
      padding:11px 14px; border-radius:16px; cursor:pointer;
      transition:all 0.15s; border:2px solid transparent; margin-bottom:7px;
    }}
    .habit-pill:hover  {{ transform:scale(1.03); }}
    .habit-pill:active {{ transform:scale(0.96); }}
    .nav-tab {{
      padding:13px 14px; border:none; background:transparent;
      font-weight:700; font-size:14px; cursor:pointer;
      transition:all 0.2s; border-bottom:3px solid transparent;
    }}
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    const {{ useState, useRef, useEffect, useCallback }} = React;

    const INIT_HABITS     = {habits_json};
    const INIT_STARS      = {stars_json};
    const INIT_CHILD_NAME = {child_name_json};
    const INIT_THEME_KEY  = {theme_key_json};

    const THEMES = {{
      rainbow: {{
        name:"🌈 Rainbow",
        boardBg:"repeating-linear-gradient(45deg,#c8a96e 0px,#c8a96e 2px,#b8956a 2px,#b8956a 20px)",
        boardBorder:"#8B6340",
        boardShadow:"inset 0 2px 8px rgba(0,0,0,0.3), 0 8px 32px rgba(0,0,0,0.25)",
        starGlow:"#FFD700", labelBg:"rgba(255,255,255,0.92)", labelColor:"#333",
        navBg:"#fff", navBorder:"#f0e0c8", primary:"#E8673A", secondary:"#4ECDC4",
        text:"#2d2d2d", subtext:"#888", card:"#fff", shadow:"0 4px 20px rgba(232,103,58,0.15)",
        habitIcons:{{default:["⭐","🌟","✨","💫","🌠"],navIcon:"🌈",boardDecor:["🌸","🦋","🌺","🎀","🌻","🎈"]}},
        emptyMsg:"Tap the board to place a star!",
        confettiColors:["#FF6B6B","#FFE66D","#4ECDC4","#FF8E53","#A8E6CF","#FFD93D"],
        pageBg:"#f5ede0",
      }},
      space: {{
        name:"🚀 Space",
        boardBg:"radial-gradient(ellipse at 20% 30%,#1a0533 0%,#0a0a2e 40%,#000510 100%)",
        boardBorder:"#2a1a5e",
        boardShadow:"inset 0 2px 8px rgba(100,50,255,0.2), 0 8px 32px rgba(0,0,0,0.6)",
        starGlow:"#00D4FF", labelBg:"rgba(10,10,46,0.92)", labelColor:"#c8e8ff",
        navBg:"#12122e", navBorder:"#2a2a6e", primary:"#7B2FBE", secondary:"#00D4FF",
        text:"#e8e8ff", subtext:"#8888bb", card:"#1a1a4e", shadow:"0 4px 20px rgba(0,212,255,0.2)",
        habitIcons:{{default:["🌟","💫","⚡","🌙","☄️"],navIcon:"🚀",boardDecor:["🪐","🌙","☄️","🛸","🔭","🌌"]}},
        emptyMsg:"Tap to launch a star into orbit!",
        confettiColors:["#00D4FF","#7B2FBE","#FF6B9D","#B8F0FF","#FFD700","#4fc3f7"],
        pageBg:"#050510",
      }},
      jungle: {{
        name:"🌿 Jungle",
        boardBg:"repeating-linear-gradient(-45deg,#5d8a3c 0px,#5d8a3c 3px,#4a7a2e 3px,#4a7a2e 22px)",
        boardBorder:"#2d5a1b",
        boardShadow:"inset 0 2px 8px rgba(0,0,0,0.3), 0 8px 32px rgba(0,0,0,0.3)",
        starGlow:"#FFD700", labelBg:"rgba(240,255,240,0.93)", labelColor:"#1b3a1b",
        navBg:"#f1f8ec", navBorder:"#c8e6c9", primary:"#2E7D32", secondary:"#8BC34A",
        text:"#1b2e1b", subtext:"#5a7a5a", card:"#ffffff", shadow:"0 4px 20px rgba(46,125,50,0.15)",
        habitIcons:{{default:["🌟","⭐","✨","💛","🌻"],navIcon:"🌿",boardDecor:["🐒","🦜","🌺","🐸","🦋","🍃"]}},
        emptyMsg:"Tap to grow your star jungle!",
        confettiColors:["#2E7D32","#8BC34A","#FF8F00","#FFF176","#A5D6A7","#FFCC02"],
        pageBg:"#e8f5e0",
      }},
      princess: {{
        name:"🩷 Princess",
        boardBg:"repeating-linear-gradient(30deg,#e8a0c0 0px,#e8a0c0 2px,#d4789c 2px,#d4789c 18px)",
        boardBorder:"#a0507a",
        boardShadow:"inset 0 2px 8px rgba(255,100,180,0.2), 0 8px 32px rgba(180,50,120,0.25)",
        starGlow:"#FF80AB", labelBg:"rgba(255,240,250,0.95)", labelColor:"#5a0040",
        navBg:"#fff0f8", navBorder:"#f8c0e0", primary:"#E91E8C", secondary:"#9C27B0",
        text:"#3a003a", subtext:"#b06090", card:"#ffffff", shadow:"0 4px 20px rgba(233,30,140,0.15)",
        habitIcons:{{default:["👑","💖","✨","🌸","💎"],navIcon:"🩷",boardDecor:["👑","💎","🌸","🦄","🎀","💐"]}},
        emptyMsg:"Tap to place a royal star!",
        confettiColors:["#E91E8C","#9C27B0","#FF80AB","#FFD6E8","#CE93D8","#F48FB1"],
        pageBg:"#fff0f6",
      }},
      safari: {{
        name:"🦁 Safari",
        boardBg:"repeating-linear-gradient(60deg,#d4a44c 0px,#d4a44c 2px,#c49040 2px,#c49040 24px)",
        boardBorder:"#8B6508",
        boardShadow:"inset 0 2px 8px rgba(0,0,0,0.3), 0 8px 32px rgba(100,60,0,0.3)",
        starGlow:"#F9A825", labelBg:"rgba(255,252,235,0.93)", labelColor:"#2d1800",
        navBg:"#fffdf5", navBorder:"#f5d9a8", primary:"#E65100", secondary:"#F9A825",
        text:"#2d1800", subtext:"#7a5c3a", card:"#fffdf5", shadow:"0 4px 20px rgba(230,81,0,0.15)",
        habitIcons:{{default:["⭐","🌟","✨","💛","🔆"],navIcon:"🦁",boardDecor:["🦁","🐘","🦒","🦓","🐆","🌴"]}},
        emptyMsg:"Tap the savanna to add a star!",
        confettiColors:["#E65100","#F9A825","#6D4C41","#FFF59D","#FFCC02","#FF8F00"],
        pageBg:"#fff8e1",
      }},
    }};

    const MILESTONES = [
      {{ stars:5,  reward:"🎉 Sticker!"       }},
      {{ stars:10, reward:"📖 Bedtime Story"  }},
      {{ stars:20, reward:"🍦 Ice Cream!"     }},
      {{ stars:30, reward:"🎠 Park Day!"      }},
      {{ stars:50, reward:"🎁 Surprise Gift!" }},
    ];

    function randBetween(a,b) {{ return a + Math.random()*(b-a); }}

    function useSoundEngine() {{
      const ctxRef = useRef(null);
      function getCtx() {{
        if (!ctxRef.current) ctxRef.current = new (window.AudioContext || window.webkitAudioContext)();
        if (ctxRef.current.state === "suspended") ctxRef.current.resume();
        return ctxRef.current;
      }}
      function playStarChime() {{
        try {{
          const ctx = getCtx();
          [523.25,659.25,783.99,1046.50].forEach((freq,i) => {{
            const osc=ctx.createOscillator(), gain=ctx.createGain();
            osc.connect(gain); gain.connect(ctx.destination);
            osc.type="sine";
            osc.frequency.setValueAtTime(freq, ctx.currentTime+i*0.1);
            gain.gain.setValueAtTime(0, ctx.currentTime+i*0.1);
            gain.gain.linearRampToValueAtTime(0.18, ctx.currentTime+i*0.1+0.02);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime+i*0.1+0.4);
            osc.start(ctx.currentTime+i*0.1);
            osc.stop(ctx.currentTime+i*0.1+0.45);
          }});
        }} catch(e) {{}}
      }}
      function playMilestoneFanfare() {{
        try {{
          const ctx = getCtx();
          const melody=[523.25,659.25,783.99,1046.50,1318.51,1046.50,1318.51];
          const times=[0,0.1,0.2,0.3,0.45,0.6,0.7];
          melody.forEach((freq,i) => {{
            const osc=ctx.createOscillator(), gain=ctx.createGain();
            osc.connect(gain); gain.connect(ctx.destination);
            osc.type="triangle";
            osc.frequency.setValueAtTime(freq, ctx.currentTime+times[i]);
            gain.gain.setValueAtTime(0, ctx.currentTime+times[i]);
            gain.gain.linearRampToValueAtTime(0.22, ctx.currentTime+times[i]+0.03);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime+times[i]+0.35);
            osc.start(ctx.currentTime+times[i]);
            osc.stop(ctx.currentTime+times[i]+0.4);
          }});
          const boom=ctx.createOscillator(), bGain=ctx.createGain();
          boom.connect(bGain); bGain.connect(ctx.destination);
          boom.type="sine";
          boom.frequency.setValueAtTime(110,ctx.currentTime);
          boom.frequency.exponentialRampToValueAtTime(55,ctx.currentTime+0.4);
          bGain.gain.setValueAtTime(0.3,ctx.currentTime);
          bGain.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+0.5);
          boom.start(ctx.currentTime);
          boom.stop(ctx.currentTime+0.55);
        }} catch(e) {{}}
      }}
      return {{ playStarChime, playMilestoneFanfare }};
    }}

    function ConfettiCanvas({{ colors, onDone }}) {{
      const canvasRef = useRef(null);
      useEffect(() => {{
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        canvas.width=window.innerWidth;
        canvas.height=window.innerHeight;
        const pieces = Array.from({{length:120}}, () => ({{
          x:randBetween(0,canvas.width), y:randBetween(-80,-10),
          w:randBetween(6,14), h:randBetween(8,18),
          color:colors[Math.floor(Math.random()*colors.length)],
          rot:randBetween(0,Math.PI*2), rotV:randBetween(-0.12,0.12),
          vx:randBetween(-2,2), vy:randBetween(2.5,6),
          opacity:1, shape:Math.random()>0.5?"rect":"circle",
        }}));
        let frame, elapsed=0;
        function draw() {{
          ctx.clearRect(0,0,canvas.width,canvas.height);
          elapsed++;
          let alive=0;
          pieces.forEach(p => {{
            p.x+=p.vx; p.y+=p.vy; p.rot+=p.rotV; p.vy+=0.08;
            if(elapsed>90) p.opacity=Math.max(0,p.opacity-0.018);
            if(p.y<canvas.height+20 && p.opacity>0) alive++;
            ctx.save(); ctx.globalAlpha=p.opacity;
            ctx.translate(p.x,p.y); ctx.rotate(p.rot); ctx.fillStyle=p.color;
            if(p.shape==="circle") {{ ctx.beginPath(); ctx.arc(0,0,p.w/2,0,Math.PI*2); ctx.fill(); }}
            else {{ ctx.fillRect(-p.w/2,-p.h/2,p.w,p.h); }}
            ctx.restore();
          }});
          if(alive>0) {{ frame=requestAnimationFrame(draw); }} else {{ onDone(); }}
        }}
        frame=requestAnimationFrame(draw);
        return () => cancelAnimationFrame(frame);
      }}, []);
      return React.createElement("canvas", {{
        ref:canvasRef,
        style:{{ position:"fixed",inset:0,zIndex:9999,pointerEvents:"none",width:"100vw",height:"100vh" }}
      }});
    }}

    function MilestoneToast({{ milestone, onDone }}) {{
      useEffect(() => {{ const t=setTimeout(onDone,3800); return ()=>clearTimeout(t); }}, []);
      return (
        <div style={{{{
          position:"fixed",top:"50%",left:"50%",
          transform:"translate(-50%,-50%)",
          background:"linear-gradient(135deg,#FFD700,#FF8C00)",
          borderRadius:28,padding:"32px 40px",textAlign:"center",
          boxShadow:"0 16px 60px rgba(0,0,0,0.35)",
          zIndex:9998,animation:"toastIn 0.4s cubic-bezier(.34,1.56,.64,1)",
          minWidth:240,
        }}}}>
          <div style={{{{fontSize:52}}}}>🏆</div>
          <div style={{{{fontSize:22,fontWeight:900,color:"#fff",marginTop:8}}}}>Milestone!</div>
          <div style={{{{fontSize:28,fontWeight:900,color:"#3a1a00",marginTop:4}}}}>{{milestone.reward}}</div>
          <div style={{{{fontSize:14,color:"#7a4000",fontWeight:700,marginTop:8}}}}>{{milestone.stars}} stars reached 🎊</div>
        </div>
      );
    }}

    function App() {{
      const [page,          setPage]         = useState("board");
      const [themeKey,      setThemeKey]     = useState(INIT_THEME_KEY);
      const [habits,        setHabits]       = useState(INIT_HABITS);
      const [boardStars,    setBoardStars]   = useState(INIT_STARS);
      const [popup,         setPopup]        = useState(null);
      const [customHabit,   setCustomHabit]  = useState("");
      const [childName,     setChildName]    = useState(INIT_CHILD_NAME);
      const [showThemePanel,setShowThemePanel] = useState(false);
      const [newHabitName,  setNewHabitName] = useState("");
      const [newHabitEmoji, setNewHabitEmoji]= useState("⭐");
      const [editingId,     setEditingId]    = useState(null);
      const [editName,      setEditName]     = useState("");
      const [editEmoji,     setEditEmoji]    = useState("");
      const [confetti,      setConfetti]     = useState(false);
      const [milestone,     setMilestone]    = useState(null);
      const boardRef  = useRef(null);
      const prevTotal = useRef(boardStars.length);
      const {{ playStarChime, playMilestoneFanfare }} = useSoundEngine();

      const T            = THEMES[themeKey] || THEMES.rainbow;
      const totalStars   = boardStars.length;
      const nextMilestone= MILESTONES.find(m => m.stars > totalStars);
      const activeHabits = habits.filter(h => h.active);

      const persist = useCallback((newStars, newHabits, newName, newTheme) => {{
        try {{
          window.parent.postMessage({{
            isStreamlitMessage: true,
            type: "streamlit:setComponentValue",
            value: {{ stars:newStars, habits:newHabits, child_name:newName, theme_key:newTheme }}
          }}, "*");
        }} catch(e) {{}}
      }}, []);

      useEffect(() => {{
        const prev=prevTotal.current, curr=totalStars;
        prevTotal.current=curr;
        if(curr<=prev) return;
        const hit=MILESTONES.find(m => m.stars===curr);
        if(hit) {{ playMilestoneFanfare(); setConfetti(true); setMilestone(hit); }}
      }}, [totalStars]);

      function handleBoardTap(e) {{
        if(popup) {{ setPopup(null); return; }}
        const rect=boardRef.current.getBoundingClientRect();
        const x=((e.clientX-rect.left)/rect.width)*100;
        const y=((e.clientY-rect.top)/rect.height)*100;
        setPopup({{ x, y, clientX:e.clientX, clientY:e.clientY }});
        setCustomHabit("");
      }}

      function placeStarForHabit(habit) {{
        if(!popup) return;
        playStarChime();
        const icons=T.habitIcons.default;
        const icon=icons[Math.floor(Math.random()*icons.length)];
        const rot=randBetween(-18,18), size=randBetween(28,44);
        const sx=popup.x+randBetween(-2,2), sy=popup.y+randBetween(-2,2);
        const newStar={{
          id: Date.now()+Math.random(),
          x: Math.max(4,Math.min(93,sx)),
          y: Math.max(4,Math.min(93,sy)),
          habitName:  habit ? habit.name  : customHabit,
          habitEmoji: habit ? habit.emoji : "⭐",
          icon, rot, size,
        }};
        const newStars=[...boardStars, newStar];
        const newHabits=habit
          ? habits.map(hb => hb.id===habit.id ? {{...hb, stars:hb.stars+1}} : hb)
          : habits;
        setBoardStars(newStars);
        setHabits(newHabits);
        setPopup(null);
        persist(newStars, newHabits, childName, themeKey);
      }}

      function placeCustomStar() {{ if(customHabit.trim()) placeStarForHabit(null); }}

      function resetBoard() {{
        if(!window.confirm("Clear all stars from the board?")) return;
        const newHabits=habits.map(x => ({{...x, stars:0}}));
        setBoardStars([]); setHabits(newHabits);
        prevTotal.current=0;
        persist([], newHabits, childName, themeKey);
      }}

      function changeTheme(key) {{
        setThemeKey(key); setShowThemePanel(false);
        persist(boardStars, habits, childName, key);
      }}

      function updateChildName(name) {{
        setChildName(name);
        persist(boardStars, habits, name, themeKey);
      }}

      function addHabit() {{
        if(!newHabitName.trim()) return;
        const newH={{id:Date.now(),name:newHabitName.trim(),emoji:newHabitEmoji||"⭐",active:true,stars:0}};
        const newHabits=[...habits, newH];
        setHabits(newHabits); setNewHabitName(""); setNewHabitEmoji("⭐");
        persist(boardStars, newHabits, childName, themeKey);
      }}

      function saveEdit(id) {{
        const newHabits=habits.map(x => x.id===id ? {{...x,name:editName,emoji:editEmoji}} : x);
        setHabits(newHabits); setEditingId(null);
        persist(boardStars, newHabits, childName, themeKey);
      }}

      function toggleHabit(id) {{
        const newHabits=habits.map(x => x.id===id ? {{...x,active:!x.active}} : x);
        setHabits(newHabits);
        persist(boardStars, newHabits, childName, themeKey);
      }}

      function deleteHabit(id) {{
        const newHabits=habits.filter(x => x.id!==id);
        setHabits(newHabits);
        persist(boardStars, newHabits, childName, themeKey);
      }}

      return (
        <div style={{{{minHeight:"100vh",background:T.pageBg,fontFamily:"'Nunito',sans-serif",color:T.text}}}}>
          {{confetti && <ConfettiCanvas colors={{{{T.confettiColors}}}} onDone={{{{()=>setConfetti(false)}}}} />}}
          {{milestone && <MilestoneToast milestone={{{{milestone}}}} onDone={{{{()=>setMilestone(null)}}}} />}}

          <nav style={{{{
            background:T.navBg, borderBottom:`2px solid ${{T.navBorder}}`,
            padding:"0 14px", display:"flex", alignItems:"center",
            justifyContent:"space-between", position:"sticky", top:0, zIndex:300,
            boxShadow:T.shadow,
          }}}}>
            <div style={{{{display:"flex"}}}}>
              {{[
                {{key:"board",     label:`${{T.habitIcons.navIcon}} Board`}},
                {{key:"dashboard", label:"📊 Dashboard"}},
                {{key:"manage",    label:"⚙️ Habits"}},
              ].map(tab=>(
                <button key={{{{tab.key}}}} className="nav-tab" onClick={{{{()=>setPage(tab.key)}}}}
                  style={{{{
                    fontFamily:"'Nunito',sans-serif",
                    color: page===tab.key ? T.primary : T.subtext,
                    borderBottom: page===tab.key ? `3px solid ${{T.primary}}` : "3px solid transparent",
                  }}}}>
                  {{tab.label}}
                </button>
              ))}}
            </div>
            <button onClick={{{{()=>setShowThemePanel(p=>!p)}}}}
              style={{{{background:T.primary,color:"#fff",border:"none",borderRadius:20,padding:"6px 14px",fontWeight:700,fontSize:13,cursor:"pointer"}}}}>
              🎨 Theme
            </button>
          </nav>

          {{showThemePanel && (
            <div style={{{{
              position:"fixed",top:54,right:12,background:T.card,borderRadius:16,
              padding:16,zIndex:400,boxShadow:"0 8px 32px rgba(0,0,0,0.22)",
              border:`2px solid ${{T.navBorder}}`,minWidth:190,
            }}}}>
              <div style={{{{fontWeight:800,fontSize:14,marginBottom:10,color:T.text}}}}>Choose Theme</div>
              {{Object.entries(THEMES).map(([key,th])=>(
                <button key={{{{key}}}} onClick={{{{()=>changeTheme(key)}}}}
                  style={{{{
                    display:"block",width:"100%",textAlign:"left",padding:"9px 14px",marginBottom:4,
                    borderRadius:10,
                    border: themeKey===key ? `2px solid ${{T.primary}}` : "2px solid transparent",
                    background: themeKey===key ? T.primary+"20" : "transparent",
                    fontWeight:700,fontSize:14,cursor:"pointer",color:T.text,
                  }}}}>
                  {{th.name}}
                </button>
              ))}}
            </div>
          )}}

          <div style={{{{maxWidth:560,margin:"0 auto",padding:"16px 14px 80px"}}}}>

            {{page==="board" && (
              <div>
                <div style={{{{textAlign:"center",marginBottom:12}}}}>
                  <div style={{{{fontSize:22,fontWeight:900,color:T.primary}}}}>{{childName}}</div>
                  <div style={{{{fontSize:13,color:T.subtext,fontWeight:600}}}}>
                    {{totalStars}} ⭐ · {{nextMilestone
                      ? `${{nextMilestone.stars-totalStars}} more → ${{nextMilestone.reward}}`
                      : "🏆 All milestones done!"}}
                  </div>
                </div>

                <div style={{{{
                  position:"relative",width:"100%",paddingTop:"75%",
                  background:T.boardBg,borderRadius:18,
                  border:`8px solid ${{T.boardBorder}}`,boxShadow:T.boardShadow,
                  cursor:"crosshair",overflow:"hidden",marginBottom:14,
                }}}} ref={{{{boardRef}}}} onClick={{{{handleBoardTap}}}}>

                  <div style={{{{
                    position:"absolute",inset:0,borderRadius:10,
                    boxShadow:"inset 0 0 30px rgba(0,0,0,0.18)",
                    pointerEvents:"none",zIndex:1,
                  }}}} />

                  {{T.habitIcons.boardDecor.map((d,i)=>{{
                    const positions=[
                      {{top:"4%",left:"3%"}},{{top:"4%",right:"3%"}},
                      {{bottom:"4%",left:"3%"}},{{bottom:"4%",right:"3%"}},
                      {{top:"4%",left:"44%"}},{{bottom:"4%",left:"44%"}},
                    ];
                    return (
                      <div key={{{{i}}}} style={{{{
                        position:"absolute",fontSize:22,...positions[i%6],
                        opacity:0.55,zIndex:2,pointerEvents:"none",
                        animation:`boardDecorFloat ${{2.5+i*0.4}}s ease-in-out infinite`,
                      }}}}>{{d}}</div>
                    );
                  }})}}

                  {{boardStars.length===0 && !popup && (
                    <div style={{{{
                      position:"absolute",inset:0,display:"flex",alignItems:"center",
                      justifyContent:"center",flexDirection:"column",gap:6,
                      zIndex:2,pointerEvents:"none",
                    }}}}>
                      <div style={{{{fontSize:36,opacity:0.4}}}}>👆</div>
                      <div style={{{{
                        fontSize:14,fontWeight:700,opacity:0.5,
                        color:themeKey==="space"?"#c8e8ff":"#fff",
                        textShadow:"0 1px 4px rgba(0,0,0,0.4)",
                        textAlign:"center",padding:"0 20px",
                      }}}}>{{T.emptyMsg}}</div>
                    </div>
                  )}}

                  {{boardStars.map(star=>(
                    <div key={{{{star.id}}}} className="board-star" title={{{{star.habitName}}}}
                      style={{{{
                        left:`${{star.x}}%`,top:`${{star.y}}%`,fontSize:star.size,
                        "--rot":`${{star.rot}}deg`,"--glow":T.starGlow,"--glow2":T.starGlow,
                        transform:`rotate(${{star.rot}}deg)`,zIndex:10,lineHeight:1,
                      }}}}>
                      {{star.icon}}
                      <div style={{{{
                        position:"absolute",top:"100%",left:"50%",
                        transform:`translateX(-50%) rotate(${{-star.rot}}deg)`,
                        background:T.labelBg,color:T.labelColor,
                        fontSize:8,fontWeight:800,whiteSpace:"nowrap",
                        padding:"1px 4px",borderRadius:4,marginTop:2,
                        boxShadow:"0 1px 4px rgba(0,0,0,0.15)",
                        maxWidth:64,overflow:"hidden",textOverflow:"ellipsis",
                      }}}}>
                        {{star.habitEmoji}} {{star.habitName}}
                      </div>
                    </div>
                  ))}}

                  {{popup && (()=>{{
                    const rect=boardRef.current?.getBoundingClientRect();
                    const popW=240;
                    const left=Math.max(0,Math.min((rect?.width??400)-popW,popup.clientX-(rect?.left??0)-popW/2));
                    const rawT=popup.clientY-(rect?.top??0)+12;
                    const above=(rect?.height??400)-rawT<170;
                    return (
                      <div onClick={{{{e=>e.stopPropagation()}}}} style={{{{
                        position:"absolute",left,
                        ...(above
                          ? {{bottom:(rect?.height??400)-(popup.clientY-(rect?.top??0))+12}}
                          : {{top:rawT}}),
                        width:popW,background:T.card,borderRadius:16,padding:"14px 12px",
                        boxShadow:"0 8px 32px rgba(0,0,0,0.28)",
                        border:`2px solid ${{T.navBorder}}`,zIndex:50,
                      }}}}>
                        <div style={{{{fontWeight:800,fontSize:13,marginBottom:10,color:T.text}}}}>
                          ⭐ Which habit earned a star?
                        </div>
                        <div style={{{{maxHeight:150,overflowY:"auto",marginBottom:8}}}}>
                          {{activeHabits.map(h=>(
                            <div key={{{{h.id}}}} className="habit-pill"
                              style={{{{background:T.primary+"18",borderColor:T.navBorder}}}}
                              onClick={{{{()=>placeStarForHabit(h)}}}}>
                              <span style={{{{fontSize:22}}}}>{{h.emoji}}</span>
                              <span style={{{{fontWeight:700,fontSize:13,color:T.text}}}}>{{h.name}}</span>
                            </div>
                          ))}}
                        </div>
                        <div style={{{{borderTop:`1px solid ${{T.navBorder}}`,paddingTop:8}}}}>
                          <div style={{{{fontSize:11,fontWeight:700,color:T.subtext,marginBottom:5}}}}>OR TYPE A HABIT</div>
                          <div style={{{{display:"flex",gap:6}}}}>
                            <input value={{{{customHabit}}}} onChange={{{{e=>setCustomHabit(e.target.value)}}}}
                              onKeyDown={{{{e=>e.key==="Enter"&&placeCustomStar()}}}}
                              placeholder="e.g. Shared toys..."
                              style={{{{
                                flex:1,padding:"7px 10px",borderRadius:10,
                                border:`1.5px solid ${{T.navBorder}}`,fontSize:12,
                                fontFamily:"'Nunito',sans-serif",
                                background:T.navBg,color:T.text,outline:"none",
                              }}}} />
                            <button onClick={{{{placeCustomStar}}}}
                              style={{{{background:T.primary,color:"#fff",border:"none",borderRadius:10,padding:"7px 12px",fontWeight:800,fontSize:16,cursor:"pointer"}}}}>
                              ⭐
                            </button>
                          </div>
                        </div>
                        <button onClick={{{{()=>setPopup(null)}}}}
                          style={{{{
                            marginTop:8,width:"100%",padding:"6px",background:"transparent",
                            border:`1.5px solid ${{T.navBorder}}`,borderRadius:10,
                            color:T.subtext,fontSize:12,fontWeight:700,cursor:"pointer",
                          }}}}>
                          Cancel
                        </button>
                      </div>
                    );
                  }})()}}
                </div>

                <div style={{{{display:"flex",gap:8}}}}>
                  <button onClick={{{{resetBoard}}}}
                    style={{{{flex:1,padding:"10px",border:`2px solid ${{T.primary}}`,background:"transparent",borderRadius:12,color:T.primary,fontWeight:800,fontSize:13,cursor:"pointer"}}}}>
                    🔄 Clear Board
                  </button>
                  <button onClick={{{{()=>setPage("dashboard")}}}}
                    style={{{{flex:1,padding:"10px",background:`linear-gradient(135deg,${{T.primary}},${{T.secondary}})`,border:"none",borderRadius:12,color:"#fff",fontWeight:800,fontSize:13,cursor:"pointer"}}}}>
                    📊 View Dashboard
                  </button>
                </div>
              </div>
            )}}

            {{page==="dashboard" && (
              <div>
                <div style={{{{textAlign:"center",marginBottom:20}}}}>
                  <div style={{{{fontSize:40}}}}>📊</div>
                  <div style={{{{fontSize:24,fontWeight:900,color:T.primary}}}}>Dashboard</div>
                </div>
                <div style={{{{
                  background:`linear-gradient(135deg,${{T.primary}},${{T.secondary}})`,
                  borderRadius:24,padding:"28px 20px",textAlign:"center",
                  color:"#fff",marginBottom:18,boxShadow:T.shadow,
                }}}}>
                  <div style={{{{fontSize:58,lineHeight:1}}}}>⭐</div>
                  <div style={{{{fontSize:52,fontWeight:900,lineHeight:1.1}}}}>{{totalStars}}</div>
                  <div style={{{{fontSize:15,fontWeight:700,opacity:0.9,marginTop:4}}}}>Total Stars on Board</div>
                  <div style={{{{fontSize:13,opacity:0.8,marginTop:2}}}}>{{childName}}</div>
                </div>
                <div style={{{{background:T.card,borderRadius:20,padding:16,boxShadow:T.shadow,marginBottom:16}}}}>
                  <div style={{{{fontWeight:800,fontSize:15,marginBottom:12}}}}>Stars by Habit</div>
                  {{habits.filter(h=>h.stars>0).length===0
                    ? <div style={{{{color:T.subtext,fontSize:14}}}}>No stars yet — tap the board!</div>
                    : habits.filter(h=>h.stars>0).sort((a,b)=>b.stars-a.stars).map(h=>(
                      <div key={{{{h.id}}}} style={{{{marginBottom:12}}}}>
                        <div style={{{{display:"flex",justifyContent:"space-between",fontSize:14,fontWeight:700,marginBottom:4}}}}>
                          <span>{{h.emoji}} {{h.name}}</span>
                          <span style={{{{color:T.primary}}}}>{{h.stars}} ⭐</span>
                        </div>
                        <div style={{{{height:10,background:T.navBorder,borderRadius:10,overflow:"hidden"}}}}>
                          <div style={{{{
                            height:"100%",borderRadius:10,
                            width:`${{Math.min((h.stars/Math.max(...habits.map(x=>x.stars),1))*100,100)}}%`,
                            background:`linear-gradient(90deg,${{T.primary}},${{T.secondary}})`,
                            transition:"width 0.5s ease",
                          }}}} />
                        </div>
                      </div>
                    ))
                  }}
                </div>
                <div style={{{{background:T.card,borderRadius:20,padding:16,boxShadow:T.shadow,marginBottom:16}}}}>
                  <div style={{{{fontWeight:800,fontSize:15,marginBottom:12}}}}>🏆 Milestones</div>
                  {{MILESTONES.map((m,i)=>{{
                    const done=totalStars>=m.stars;
                    const mc=["#FFD700","#4ECDC4","#FF6B9D","#7B2FBE","#FF6B6B"];
                    return (
                      <div key={{{{m.stars}}}} style={{{{
                        display:"flex",alignItems:"center",gap:12,padding:"10px 0",
                        borderBottom:i<MILESTONES.length-1?`1px solid ${{T.navBorder}}`:"none",
                        opacity:done?1:0.5,
                      }}}}>
                        <div style={{{{
                          width:36,height:36,borderRadius:"50%",
                          background:done?mc[i]:T.navBorder,
                          display:"flex",alignItems:"center",justifyContent:"center",fontSize:18,
                        }}}}>{{done?"✅":"🔒"}}</div>
                        <div style={{{{flex:1}}}}>
                          <div style={{{{fontWeight:700,fontSize:14}}}}>{{m.reward}}</div>
                          <div style={{{{fontSize:12,color:T.subtext}}}}>{{m.stars}} stars needed</div>
                        </div>
                        {{done && <div style={{{{fontSize:11,fontWeight:800,color:mc[i]}}}}>EARNED!</div>}}
                      </div>
                    );
                  }}}}
                </div>
                <button onClick={{{{resetBoard}}}}
                  style={{{{width:"100%",padding:"13px",border:`2px solid ${{T.primary}}`,background:"transparent",borderRadius:14,color:T.primary,fontWeight:800,fontSize:14,cursor:"pointer"}}}}>
                  🔄 Reset All Stars
                </button>
              </div>
            )}}

            {{page==="manage" && (
              <div>
                <div style={{{{textAlign:"center",marginBottom:20}}}}>
                  <div style={{{{fontSize:40}}}}>⚙️</div>
                  <div style={{{{fontSize:24,fontWeight:900,color:T.primary}}}}>Manage Habits</div>
                </div>
                <div style={{{{background:T.card,borderRadius:20,padding:16,boxShadow:T.shadow,marginBottom:16}}}}>
                  <div style={{{{fontWeight:800,marginBottom:8}}}}>👶 Child's Name</div>
                  <input value={{{{childName}}}} onChange={{{{e=>updateChildName(e.target.value)}}}}
                    placeholder="Enter name..."
                    style={{{{
                      width:"100%",padding:"10px 14px",borderRadius:12,
                      border:`2px solid ${{T.navBorder}}`,fontFamily:"'Nunito',sans-serif",
                      fontSize:15,fontWeight:700,color:T.text,
                      background:T.navBg,outline:"none",boxSizing:"border-box",
                    }}}} />
                </div>
                <div style={{{{background:T.card,borderRadius:20,padding:16,boxShadow:T.shadow,marginBottom:16}}}}>
                  <div style={{{{fontWeight:800,marginBottom:10}}}}>➕ Add Habit</div>
                  <div style={{{{display:"flex",gap:8,marginBottom:10}}}}>
                    <input value={{{{newHabitEmoji}}}} onChange={{{{e=>setNewHabitEmoji(e.target.value)}}}}
                      style={{{{
                        width:56,padding:"9px",borderRadius:12,textAlign:"center",
                        border:`2px solid ${{T.navBorder}}`,fontSize:20,
                        background:T.navBg,color:T.text,outline:"none",
                      }}}} />
                    <input value={{{{newHabitName}}}} onChange={{{{e=>setNewHabitName(e.target.value)}}}}
                      placeholder="Habit name..."
                      onKeyDown={{{{e=>e.key==="Enter"&&addHabit()}}}}
                      style={{{{
                        flex:1,padding:"9px 12px",borderRadius:12,
                        border:`2px solid ${{T.navBorder}}`,fontSize:14,
                        fontFamily:"'Nunito',sans-serif",
                        background:T.navBg,color:T.text,outline:"none",
                      }}}} />
                  </div>
                  <button onClick={{{{addHabit}}}}
                    style={{{{
                      width:"100%",padding:"11px",
                      background:`linear-gradient(135deg,${{T.primary}},${{T.secondary}})`,
                      border:"none",borderRadius:12,color:"#fff",fontWeight:800,fontSize:14,cursor:"pointer",
                    }}}}>
                    Add Habit
                  </button>
                </div>
                <div style={{{{background:T.card,borderRadius:20,padding:16,boxShadow:T.shadow}}}}>
                  <div style={{{{fontWeight:800,marginBottom:12}}}}>📋 Habits ({{habits.length}})</div>
                  {{habits.map(h=>(
                    <div key={{{{h.id}}}} style={{{{borderBottom:`1px solid ${{T.navBorder}}`,paddingBottom:12,marginBottom:12}}}}>
                      {{editingId===h.id ? (
                        <div style={{{{display:"flex",gap:8,alignItems:"center"}}}}>
                          <input value={{{{editEmoji}}}} onChange={{{{e=>setEditEmoji(e.target.value)}}}}
                            style={{{{width:48,padding:"7px",borderRadius:10,textAlign:"center",border:`2px solid ${{T.primary}}`,fontSize:18,background:T.navBg,color:T.text,outline:"none"}}}} />
                          <input value={{{{editName}}}} onChange={{{{e=>setEditName(e.target.value)}}}}
                            style={{{{flex:1,padding:"7px 10px",borderRadius:10,border:`2px solid ${{T.primary}}`,fontSize:13,fontFamily:"'Nunito',sans-serif",background:T.navBg,color:T.text,outline:"none"}}}} />
                          <button onClick={{{{()=>saveEdit(h.id)}}}}
                            style={{{{background:T.secondary,border:"none",borderRadius:8,padding:"7px 11px",color:"#fff",fontWeight:700,cursor:"pointer"}}}}>✓</button>
                          <button onClick={{{{()=>setEditingId(null)}}}}
                            style={{{{background:T.subtext,border:"none",borderRadius:8,padding:"7px 9px",color:"#fff",fontWeight:700,cursor:"pointer"}}}}>✕</button>
                        </div>
                      ) : (
                        <div style={{{{display:"flex",alignItems:"center",gap:10}}}}>
                          <span style={{{{fontSize:26}}}}>{{h.emoji}}</span>
                          <div style={{{{flex:1}}}}>
                            <div style={{{{fontWeight:700,fontSize:14,color:h.active?T.text:T.subtext,textDecoration:h.active?"none":"line-through"}}}}>{{h.name}}</div>
                            <div style={{{{fontSize:11,color:T.subtext}}}}>{{h.stars}} ⭐ earned</div>
                          </div>
                          <button onClick={{{{()=>toggleHabit(h.id)}}}}
                            style={{{{padding:"4px 9px",borderRadius:20,border:"none",background:h.active?T.secondary+"33":T.navBorder,color:h.active?T.secondary:T.subtext,fontSize:11,fontWeight:800,cursor:"pointer"}}}}>
                            {{h.active?"ON":"OFF"}}
                          </button>
                          <button onClick={{{{()=>{{setEditingId(h.id);setEditName(h.name);setEditEmoji(h.emoji);}}}}}}
                            style={{{{width:30,height:30,borderRadius:8,border:"none",background:T.navBorder,cursor:"pointer",fontSize:14}}}}>✏️</button>
                          <button onClick={{{{()=>deleteHabit(h.id)}}}}
                            style={{{{width:30,height:30,borderRadius:8,border:"none",background:"#ffebee",cursor:"pointer",fontSize:14}}}}>🗑️</button>
                        </div>
                      )}}
                    </div>
                  ))}}
                </div>
              </div>
            )}}
          </div>
        </div>
      );
    }}

    ReactDOM.createRoot(document.getElementById('root')).render(<App />);
  </script>
</body>
</html>"""

# ─── 5. WRITE HTML & DECLARE COMPONENT ─────────────────────────────────────
PARENT_DIR    = os.path.dirname(os.path.abspath(__file__))
COMPONENT_DIR = os.path.join(PARENT_DIR, "tracker_frontend")
os.makedirs(COMPONENT_DIR, exist_ok=True)

html_final = build_html(
    st.session_state["habits_data"],
    st.session_state["stars_data"],
    st.session_state["child_name"],
    st.session_state["theme_key"],
)

html_path    = os.path.join(COMPONENT_DIR, "index.html")
content_hash = hashlib.md5(html_final.encode()).hexdigest()

if content_hash != st.session_state.get("html_hash", ""):
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_final)
    st.session_state["html_hash"] = content_hash

# ─── 6. RENDER COMPONENT & HANDLE RESPONSE ──────────────────────────────────
tracker_comp = components.declare_component("tracker", path=COMPONENT_DIR)
val = tracker_comp(key="main_tracker", default=None)

if val is not None:
    new_habits     = val.get("habits",     st.session_state["habits_data"])
    new_stars      = val.get("stars",      st.session_state["stars_data"])
    new_child_name = val.get("child_name", st.session_state["child_name"])
    new_theme_key  = val.get("theme_key",  st.session_state["theme_key"])

    new_state  = {"habits":new_habits,"stars":new_stars,"name":new_child_name,"theme":new_theme_key}
    state_hash = hashlib.md5(json.dumps(new_state, sort_keys=True).encode()).hexdigest()

    if state_hash != st.session_state.get("last_hash", ""):
        st.session_state["last_hash"]   = state_hash
        st.session_state["habits_data"] = new_habits
        st.session_state["stars_data"]  = new_stars
        st.session_state["child_name"]  = new_child_name
        st.session_state["theme_key"]   = new_theme_key
        save_cloud_data(new_habits, new_stars, new_child_name, new_theme_key)
        st.rerun()
