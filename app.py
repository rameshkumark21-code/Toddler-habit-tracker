import streamlit as st
import streamlit.components.v1 as components
import json
import pandas as pd
import os
import hashlib

# Standard Page Configuration must be the absolute first Streamlit command
st.set_page_config(
    page_title="Star Habit Tracker",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit canvas wrapper elements & clean out padding parameters
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

# 1. Initialize the secure Google Sheets connection from secrets automatically
try:
    conn = st.connection("gsheets", type=st.connections.GSheetsConnection)
except Exception:
    conn = None

def load_cloud_data():
    """Loads all tracking data directly from the Google Sheet tabs via Secrets configuration."""
    default_habits = [
        {"id": 1, "name": "Brushed Teeth", "emoji": "🦷", "active": True, "stars": 0},
        {"id": 2, "name": "Ate Vegetables", "emoji": "🥦", "active": True, "stars": 0},
        {"id": 3, "name": "Said Please & Thank You", "emoji": "🙏", "active": True, "stars": 0},
        {"id": 4, "name": "Slept on Time", "emoji": "😴", "active": True, "stars": 0},
        {"id": 5, "name": "Cleaned Up Toys", "emoji": "🧸", "active": True, "stars": 0},
        {"id": 6, "name": "Washed Hands", "emoji": "🤲", "active": True, "stars": 0}
    ]
    
    if conn is not None:
        try:
            try:
                habits_df = conn.read(worksheet="Habits")
                if habits_df is not None and not habits_df.empty:
                    # Clean up NaN values to prevent raw NaN JS compilation breakages
                    habits_df = habits_df.fillna("")
                    # Re-verify active column maps cleanly to true booleans
                    if "active" in habits_df.columns:
                        habits_df["active"] = habits_df["active"].apply(lambda x: x in [True, 1, "True", "true", "ON", "on"])
                    habits = habits_df.to_dict(orient="records")
                else:
                    habits = default_habits
            except Exception:
                habits = default_habits

            try:
                stars_df = conn.read(worksheet="Stars")
                if stars_df is not None and not stars_df.empty:
                    stars_df = stars_df.fillna("")
                    stars = stars_df.to_dict(orient="records")
                else:
                    stars = []
            except Exception:
                stars = []
            
            try:
                settings_df = conn.read(worksheet="Settings")
                child_name = settings_df.iloc[0]["child_name"] if (settings_df is not None and not settings_df.empty) else "My Star!"
            except Exception:
                child_name = "My Star!"
            
            return habits, stars, child_name
        except Exception:
            return default_habits, [], "My Star!"
            
    return default_habits, [], "My Star!"

# Load current cloud state cleanly before page paint
cloud_habits, cloud_stars, cloud_name = load_cloud_data()

# =====================================================================
# 2. RAW INTERACTIVE ENGINE WITH BI-DIRECTIONAL DATA BRIDGE
# =====================================================================
html_code = """
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
</head>
<body style="margin: 0; padding: 0;">
  <div id="root"></div>

  <script type="text/babel">
    const { useState, useRef, useEffect } = React;

    const INITIAL_HABITS_DATA = INITIAL_HABITS_PLACEHOLDER;
    const INITIAL_STARS_DATA = INITIAL_STARS_PLACEHOLDER;
    const INITIAL_NAME_DATA = INITIAL_NAME_PLACEHOLDER;

    const THEMES = {
      rainbow: {
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
        habitIcons: { default: ["⭐","🌟","✨","💫","🌠"], navIcon: "🌈", boardDecor: ["🌸","🦋","🌺","🎀","🌻","🎈"] },
        emptyMsg: "Tap the board to place a star!",
      },
      space: {
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
        habitIcons: { default: ["🌟","💫","⚡","🌙","☄️"], navIcon: "🚀", boardDecor: ["🪐","🌙","☄️","🛸","🔭","🌌"] },
        emptyMsg: "Tap to launch a star into orbit!",
      },
      jungle: {
        name: "🌿 Jungle",
        boardBg: `repeating-linear-gradient(-45deg, #5d8a3c 0px, #5d8a3c 3px, #4a7a2e 3px, #4a7a2e 22px)`,
        boardBorder: "#2d5a1b",
        boardShadow: "inset 0 2px 8px rgba(0,0,0,0.3), 0 8px 32px rgba(0,0,0,0.3)",
        starGlow: "#FFD700",
        labelBg: "rgba(240,255,240,0.93)",
        labelColor: "#1b3a1b",
        navBg: "#f1f8ec",
        navBorder: "#c8e6c9",
        primary: "#2E7D32",
        secondary: "#8BC34A",
        text: "#1b2e1b",
        subtext: "#5a7a5a",
        card: "#ffffff",
        shadow: "0 4px 20px rgba(46,125,50,0.15)",
        font: "'Nunito', sans-serif",
        habitIcons: { default: ["🌟","⭐","✨","💛","🌻"], navIcon: "🌿", boardDecor: ["🐒","🦜","🌺","🐸","🦋","🍃"] },
        emptyMsg: "Tap to grow your star jungle!",
      },
      princess: {
        name: "🩷 Princess",
        boardBg: `repeating-linear-gradient(30deg, #e8a0c0 0px, #e8a0c0 2px, #d4789c 2px, #d4789c 18px)`,
        boardBorder: "#a0507a",
        boardShadow: "inset 0 2px 8px rgba(255,100,180,0.2), 0 8px 32px rgba(180,50,120,0.25)",
        starGlow: "#FF80AB",
        labelBg: "rgba(255,240,250,0.95)",
        labelColor: "#5a0040",
        navBg: "#fff0f8",
        navBorder: "#f8c0e0",
        primary: "#E91E8C",
        secondary: "#9C27B0",
        text: "#3a003a",
        subtext: "#b06090",
        card: "#ffffff",
        shadow: "0 4px 20px rgba(233,30,140,0.15)",
        font: "'Nunito', sans-serif",
        habitIcons: { default: ["👑","💖","✨","🌸","💎"], navIcon: "🩷", boardDecor: ["👑","💎","🌸","🦄","🎀","💐"] },
        emptyMsg: "Tap to place a royal star!",
      },
      safari: {
        name: "🦁 Safari",
        boardBg: `repeating-linear-gradient(60deg, #d4a44c 0px, #d4a44c 2px, #c49040 2px, #c49040 24px)`,
        boardBorder: "#8B6508",
        boardShadow: "inset 0 2px 8px rgba(0,0,0,0.3), 0 8px 32px rgba(100,60,0,0.3)",
        starGlow: "#F9A825",
        labelBg: "rgba(255,252,235,0.93)",
        labelColor: "#2d1800",
        navBg: "#fffdf5",
        navBorder: "#f5d9a8",
        primary: "#E65100",
        secondary: "#F9A825",
        text: "#2d1800",
        subtext: "#7a5c3a",
        card: "#fffdf5",
        shadow: "0 4px 20px rgba(230,81,0,0.15)",
        font: "'Nunito', sans-serif",
        habitIcons: { default: ["⭐","🌟","✨","💛","🔆"], navIcon: "🦁", boardDecor: ["🦁","🐘","🦒","🦓","🐆","🌴"] },
        emptyMsg: "Tap the savanna to add a star!",
      },
    };

    const DEFAULT_MILESTONES = [
      { stars: 5,  reward: "🎉 Sticker!" },
      { stars: 10, reward: "📖 Bedtime Story" },
      { stars: 20, reward: "🍦 Ice Cream!" },
      { stars: 30, reward: "🎠 Park Day!" },
      { stars: 50, reward: "🎁 Surprise Gift!" },
    ];

    function randBetween(a, b) { return a + Math.random() * (b - a); }

    function App() {
      const [page, setPage]           = useState("board");
      const [themeKey, setThemeKey]   = useState("rainbow");
      
      // FIXED: Prioritize standard cloud data stream over local storage mirrors
      const [habits, setHabits]       = useState(INITIAL_HABITS_DATA);
      const [boardStars, setBoardStars] = useState(INITIAL_STARS_DATA);
      const [childName, setChildName] = useState(INITIAL_NAME_DATA);
      
      const [milestones, setMilestones] = useState(() => {
        const local = localStorage.getItem("star_tracker_milestones");
        return local ? JSON.parse(local) : DEFAULT_MILESTONES;
      });

      const [popup, setPopup]         = useState(null); 
      const [selectedHabitId, setSelectedHabitId] = useState("custom");
      const [customHabit, setCustomHabit] = useState("");
      const [showThemePanel, setShowThemePanel] = useState(false);
      const [newHabitName, setNewHabitName]   = useState("");
      const [newHabitEmoji, setNewHabitEmoji] = useState("⭐");
      const [editingId, setEditingId] = useState(null);
      const [editName, setEditName]   = useState("");
      const [editEmoji, setEditEmoji] = useState("");
      const boardRef = useRef(null);

      const T = THEMES[themeKey];
      const totalStars = boardStars.length;
      const sortedMilestones = [...milestones].sort((a, b) => a.stars - b.stars);
      const nextMilestone = sortedMilestones.find(m => m.stars > totalStars);

      useEffect(() => {
        if (window.parent) {
          window.parent.postMessage({ type: "streamlit:componentReady", version: 1 }, "*");
          window.parent.postMessage({ type: "streamlit:setFrameHeight", height: 850 }, "*");
        }
      }, []);

      const syncWithPythonCloud = (updatedHabits, updatedStars, updatedName) => {
        if (window.parent) {
          window.parent.postMessage({
            isStreamlitMessage: true,
            type: "streamlit:setComponentValue",
            value: { habits: updatedHabits, stars: updatedStars, child_name: updatedName }
          }, "*");
        }
      };

      const saveHabits = (newH) => { 
        setHabits(newH); 
        localStorage.setItem("star_tracker_habits", JSON.stringify(newH)); 
        syncWithPythonCloud(newH, boardStars, childName);
      };
      const saveStars = (newS) => { 
        setBoardStars(newS); 
        localStorage.setItem("star_tracker_stars", JSON.stringify(newS)); 
        syncWithPythonCloud(habits, newS, childName);
      };
      const saveName = (name) => { 
        setChildName(name); 
        localStorage.setItem("star_tracker_name", name); 
        syncWithPythonCloud(habits, boardStars, name);
      };
      const saveMilestones = (newM) => { 
        setMilestones(newM); 
        localStorage.setItem("star_tracker_milestones", JSON.stringify(newM)); 
      };

      function handleBoardTap(e) {
        if (popup) { setPopup(null); return; }
        const rect = boardRef.current.getBoundingClientRect();
        const clientX = e.clientX || (e.touches && e.touches[0].clientX);
        const clientY = e.clientY || (e.touches && e.touches[0].clientY);
        if(!clientX || !clientY) return;

        const x = ((clientX - rect.left) / rect.width) * 100;
        const y = ((clientY - rect.top)  / rect.height) * 100;
        
        setPopup({ x, y, clientX, clientY });
        const activeHabits = habits.filter(h => h.active);
        setSelectedHabitId(activeHabits.length > 0 ? activeHabits[0].id.toString() : "custom");
        setCustomHabit("");
      }

      function submitStar() {
        if (!popup) return;
        
        let targetHabit = null;
        let finalName = customHabit.trim();
        let finalEmoji = "⭐";

        if (selectedHabitId !== "custom") {
          targetHabit = habits.find(h => h.id.toString() === selectedHabitId);
          if (targetHabit) {
            finalName = targetHabit.name;
            finalEmoji = targetHabit.emoji;
          }
        }

        if (!finalName) return; 

        const icons = T.habitIcons.default;
        const icon = icons[Math.floor(Math.random() * icons.length)];
        const rot  = randBetween(-18, 18);
        const size = randBetween(28, 44);
        const sx = popup.x + randBetween(-3, 3);
        const sy = popup.y + randBetween(-3, 3);

        const newStar = {
          id: Date.now() + Math.random(),
          x: Math.max(4, Math.min(94, sx)),
          y: Math.max(4, Math.min(94, sy)),
          habitId: targetHabit ? targetHabit.id : null,
          habitName: finalName,
          habitEmoji: finalEmoji,
          icon, rot, size,
        };

        const updatedStars = [...boardStars, newStar];
        let updatedHabits = habits;

        if (targetHabit) {
          updatedHabits = habits.map(hb => hb.id === targetHabit.id ? { ...hb, stars: hb.stars + 1 } : hb);
        }

        setBoardStars(updatedStars);
        setHabits(updatedHabits);
        localStorage.setItem("star_tracker_stars", JSON.stringify(updatedStars));
        localStorage.setItem("star_tracker_habits", JSON.stringify(updatedHabits));
        
        syncWithPythonCloud(updatedHabits, updatedStars, childName);
        setPopup(null);
      }

      function handleMilestoneChange(index, field, value) {
        const updated = milestones.map((m, i) => {
          if (i === index) {
            return { ...m, [field]: field === "stars" ? parseInt(value, 10) || 0 : value };
          }
          return m;
        });
        saveMilestones(updated);
      }

      function resetBoard() {
        if (window.confirm("Clear all stars from the board?")) {
          const updatedStars = [];
          const updatedHabits = habits.map(x => ({ ...x, stars: 0 }));
          setBoardStars(updatedStars);
          setHabits(updatedHabits);
          localStorage.setItem("star_tracker_stars", JSON.stringify(updatedStars));
          localStorage.setItem("star_tracker_habits", JSON.stringify(updatedHabits));
          syncWithPythonCloud(updatedHabits, updatedStars, childName);
        }
      }

      const activeHabits = habits.filter(h => h.active);
      const decorItems = T.habitIcons.boardDecor;

      return (
        <div style={{ minHeight: "100vh", background: themeKey === "space" ? "#050510" : "#f5ede0", fontFamily: T.font, color: T.text, transition: "background 0.3s" }}>
          <style>{`
            @keyframes floatIn {
              0%   { transform: scale(0) rotate(var(--rot)) translateY(8px); opacity: 0; }
              60%  { transform: scale(1.3) rotate(var(--rot)) translateY(-4px); opacity: 1; }
              100% { transform: scale(1) rotate(var(--rot)) translateY(0); opacity: 1; }
            }
            @keyframes pulse {
              0%, 100% { filter: brightness(1); }
              50%       { filter: brightness(1.4); }
            }
            @keyframes boardDecorFloat {
              0%, 100% { transform: translateY(0px); }
              50%       { transform: translateY(-5px); }
            }
            .board-star {
              position: absolute; cursor: default;
              animation: floatIn 0.45s cubic-bezier(.34,1.56,.64,1) forwards, pulse 2.5s ease-in-out infinite 0.5s;
              user-select: none; pointer-events: none;
            }
            .nav-tab {
              padding: 13px 14px; border: none; background: transparent;
              font-weight: 700; font-size: 14px; cursor: pointer; transition: all 0.2s;
              border-bottom: 3px solid transparent;
            }
            .theme-btn { transition: transform 0.15s; }
            .theme-btn:hover { transform: scale(1.04); }
            .milestone-input {
              border: 1px solid transparent; background: transparent;
              font-family: inherit; font-size: inherit; font-weight: inherit;
              color: inherit; width: 100%; border-radius: 4px; padding: 2px 4px;
            }
            .milestone-input:focus { background: rgba(0,0,0,0.05); border-color: #888; outline: none; }
          `}</style>

          {/* ── NAV BAR ── */}
          <nav style={{ background: T.navBg, borderBottom: `2px solid ${T.navBorder}`, padding: "0 14px", display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 300, boxShadow: T.shadow }}>
            <div style={{ display: "flex", gap: 0 }}>
              {[
                { key: "board",     label: `${T.habitIcons.navIcon} Board` },
                { key: "dashboard", label: "📊 Dashboard" },
                { key: "manage",    label: "⚙️ Habits" },
              ].map(tab => (
                <button key={tab.key} className="nav-tab" onClick={() => setPage(tab.key)} style={{ fontFamily: T.font, color: page === tab.key ? T.primary : T.subtext, borderBottom: page === tab.key ? `3px solid ${T.primary}` : "3px solid transparent" }}>{tab.label}</button>
              ))}
            </div>
            <button onClick={() => setShowThemePanel(p => !p)} style={{ background: T.primary, color: "#fff", border: "none", borderRadius: 20, padding: "6px 14px", fontWeight: 700, fontSize: 13, cursor: "pointer", fontFamily: T.font }}>🎨 Theme</button>
          </nav>

          {/* ── LIVE MULTI-THEME SELECTOR PANEL ── */}
          {showThemePanel && (
            <div style={{ position: "fixed", top: 54, right: 12, background: T.card, borderRadius: 16, padding: 16, zIndex: 400, boxShadow: "0 8px 32px rgba(0,0,0,0.22)", border: `2px solid ${T.navBorder}`, minWidth: 190 }}>
              <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 10, color: T.text }}>Choose Theme</div>
              {Object.entries(THEMES).map(([key, th]) => (
                <button key={key} className="theme-btn" onClick={() => { setThemeKey(key); setShowThemePanel(false); }} style={{ display: "block", width: "100%", textAlign: "left", padding: "9px 14px", marginBottom: 4, borderRadius: 10, border: themeKey === key ? `2px solid ${T.primary}` : "2px solid transparent", background: themeKey === key ? T.primary + "20" : "transparent", fontWeight: 700, fontSize: 14, cursor: "pointer", color: T.text, fontFamily: T.font }}>{th.name}</button>
              ))}
            </div>
          )}

          <div style={{ maxWidth: 560, margin: "0 auto", padding: "16px 14px 80px" }}>

            {/* ══ VIEW: INTERACTIVE BOARD ══ */}
            {page === "board" && (
              <div>
                <div style={{ textAlign: "center", marginBottom: 14 }}>
                  <div style={{ fontSize: 22, fontWeight: 900, color: T.primary }}>{childName}</div>
                  <div style={{ fontSize: 13, color: T.subtext, fontWeight: 600 }}>
                    {totalStars} ⭐ • {nextMilestone ? `${nextMilestone.stars - totalStars} more → ${nextMilestone.reward}` : "🏆 All milestones done!"}
                  </div>
                </div>

                <div style={{ position: "relative", width: "100%", paddingTop: "75%", background: T.boardBg, borderRadius: 18, border: `8px solid ${T.boardBorder}`, boxShadow: T.boardShadow, cursor: "crosshair", overflow: "hidden", marginBottom: 14 }} ref={boardRef} onClick={handleBoardTap}>
                  <div style={{ position: "absolute", inset: 0, borderRadius: 10, boxShadow: "inset 0 0 30px rgba(0,0,0,0.18)", pointerEvents: "none", zIndex: 1 }} />

                  {decorItems.map((d, i) => {
                    const positions = [{ top: "4%", left: "3%" }, { top: "4%", right: "3%" }, { bottom: "4%", left: "3%" }, { bottom: "4%", right:"3%" }];
                    return <div key={i} style={{ position: "absolute", fontSize: 22, ...positions[i % positions.length], opacity: 0.55, zIndex: 2, pointerEvents: "none", animation: `boardDecorFloat ${2.5 + i * 0.4}s ease-in-out infinite` }}>{d}</div>;
                  })}

                  {boardStars.length === 0 && !popup && (
                    <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 6, zIndex: 2, pointerEvents: "none" }}>
                      <div style={{ fontSize: 36, opacity: 0.4 }}>👆</div>
                      <div style={{ fontSize: 14, fontWeight: 700, opacity: 0.5, color: themeKey === "space" ? "#c8e8ff" : "#fff", textShadow: "0 1px 4px rgba(0,0,0,0.4)", textAlign: "center", padding: "0 20px" }}>{T.emptyMsg}</div>
                    </div>
                  )}

                  {boardStars.map(star => (
                    <div key={star.id} className="board-star" style={{ left: `${star.x}%`, top: `${star.y}%`, fontSize: star.size, "--rot": `${star.rot}deg`, transform: `rotate(${star.rot}deg)`, filter: `drop-shadow(0 0 6px ${T.starGlow}) drop-shadow(0 0 14px ${T.starGlow}88)`, zIndex: 10, lineHeight: 1 }}>
                      {star.icon}
                      <div style={{ position: "absolute", top: "100%", left: "50%", transform: `translateX(-50%) rotate(${-star.rot}deg)`, background: T.labelBg, color: T.labelColor, fontSize: 8, fontWeight: 800, whiteSpace: "nowrap", padding: "1px 4px", borderRadius: 4, marginTop: 2, boxShadow: "0 1px 4px rgba(0,0,0,0.15)", maxWidth: 60, overflow: "hidden", textOverflow: "ellipsis" }}>{star.habitEmoji} {star.habitName}</div>
                    </div>
                  ))}

                  {/* ── RESPONSIVE PLACEMENT DROPDOWN ── */}
                  {popup && (() => {
                    const rect = boardRef.current?.getBoundingClientRect();
                    const popW = 250;
                    const rawLeft = popup.clientX - (rect?.left ?? 0) - popW / 2;
                    const clampedLeft = Math.max(0, Math.min((rect?.width ?? 400) - popW, rawLeft));
                    const rawTop  = popup.clientY - (rect?.top ?? 0) + 12;
                    const fromBottom = (rect?.height ?? 400) - rawTop;
                    return (
                      <div onClick={e => e.stopPropagation()} style={{ position: "absolute", left: clampedLeft, ...(fromBottom < 170 ? { bottom: (rect?.height ?? 400) - (popup.clientY - (rect?.top ?? 0)) + 12 } : { top: rawTop }), width: popW, background: T.card, borderRadius: 16, padding: "14px 12px", boxShadow: "0 8px 32px rgba(0,0,0,0.28)", border: `2px solid ${T.navBorder}`, zIndex: 50 }}>
                        <div style={{ fontWeight: 800, fontSize: 13, marginBottom: 8, color: T.text }}>⭐ Select earned habit:</div>
                        
                        <select value={selectedHabitId} onChange={e => setSelectedHabitId(e.target.value)} style={{ width: "100%", padding: "8px 10px", borderRadius: 10, border: `1.5px solid ${T.navBorder}`, background: T.navBg, color: T.text, fontSize: 14, fontWeight: 600, outline: "none", marginBottom: 10 }}>
                          {activeHabits.map(h => <option key={h.id} value={h.id}>{h.emoji} {h.name}</option>)}
                          <option value="custom">➕ Custom...</option>
                        </select>

                        {selectedHabitId === "custom" && (
                          <div style={{ marginBottom: 10 }}>
                            <input value={customHabit} onChange={e => setCustomHabit(e.target.value)} onKeyDown={e => e.key === "Enter" && submitStar()} placeholder="Type custom habit..." style={{ width: "100%", padding: "8px 10px", borderRadius: 10, border: `1.5px solid ${T.navBorder}`, fontSize: 13, fontFamily: T.font, background: T.navBg, color: T.text, outline: "none", boxSizing: "border-box" }} />
                          </div>
                        )}

                        <div style={{ display: "flex", gap: 6 }}>
                          <button onClick={() => setPopup(null)} style={{ flex: 1, padding: "8px", background: "transparent", border: `1.5px solid ${T.navBorder}`, borderRadius: 10, color: T.subtext, fontSize: 13, fontWeight: 700, cursor: "pointer", fontFamily: T.font }}>Cancel</button>
                          <button onClick={submitStar} style={{ flex: 1, padding: "8px", background: T.primary, border: "none", borderRadius: 10, color: "#fff", fontSize: 13, fontWeight: 800, cursor: "pointer", fontFamily: T.font }}>Add Star</button>
                        </div>
                      </div>
                    );
                  })()}
                </div>

                <div style={{ display: "flex", gap: 8 }}>
                  <button onClick={resetBoard} style={{ flex: 1, padding: "10px", border: `2px solid ${T.primary}`, background: "transparent", borderRadius: 12, color: T.primary, fontWeight: 800, fontSize: 13, cursor: "pointer", fontFamily: T.font }}>🔄 Clear Board</button>
                  <button onClick={() => setPage("dashboard")} style={{ flex: 1, padding: "10px", background: `linear-gradient(135deg, ${T.primary}, ${T.secondary})`, border: "none", borderRadius: 12, color: "#fff", fontWeight: 800, fontSize: 13, cursor: "pointer", fontFamily: T.font }}>📊 View Dashboard</button>
                </div>
              </div>
            )}

            {/* ══ VIEW: STATS & DASHBOARD ══ */}
            {page === "dashboard" && (
              <div>
                <div style={{ textAlign: "center", marginBottom: 20 }}>
                  <div style={{ fontSize: 40 }}>📊</div>
                  <div style={{ fontSize: 24, fontWeight: 900, color: T.primary }}>Dashboard</div>
                </div>
                <div style={{ background: `linear-gradient(135deg, ${T.primary}, ${T.secondary})`, borderRadius: 24, padding: "28px 20px", textAlign: "center", color: "#fff", marginBottom: 18, boxShadow: T.shadow }}>
                  <div style={{ fontSize: 58, lineHeight: 1 }}>⭐</div>
                  <div style={{ fontSize: 52, fontWeight: 900, lineHeight: 1.1 }}>{totalStars}</div>
                  <div style={{ fontSize: 15, fontWeight: 700, opacity: 0.9, marginTop: 4 }}>Total Stars on Board</div>
                </div>

                <div style={{ background: T.card, borderRadius: 20, padding: 16, boxShadow: T.shadow, marginBottom: 16 }}>
                  <div style={{ fontWeight: 800, fontSize: 15, marginBottom: 12 }}>Stars by Habit</div>
                  {habits.filter(h => h.stars > 0).length === 0 ? (
                    <div style={{ color: T.subtext, fontSize: 14 }}>No stars yet — tap the board!</div>
                  ) : (
                    habits.filter(h => h.stars > 0).sort((a, b) => b.stars - a.stars).map(h => (
                      <div key={h.id} style={{ marginBottom: 12 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 14, fontWeight: 700, marginBottom: 4 }}>
                          <span>{h.emoji} {h.name}</span>
                          <span style={{ color: T.primary }}>{h.stars} ⭐</span>
                        </div>
                        <div style={{ height: 10, background: T.navBorder, borderRadius: 10, overflow: "hidden" }}>
                          <div style={{ height: "100%", borderRadius: 10, width: `${Math.min((h.stars / Math.max(...habits.map(x => x.stars), 1)) * 100, 100)}%`, background: `linear-gradient(90deg, ${T.primary}, ${T.secondary})`, transition: "width 0.5s ease" }} />
                        </div>
                      </div>
                    ))
                  )}
                </div>

                <div style={{ background: T.card, borderRadius: 20, padding: 16, boxShadow: T.shadow, marginBottom: 16 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                    <div style={{ fontWeight: 800, fontSize: 15 }}>🏆 Milestones</div>
                  </div>
                  {milestones.map((m, i) => {
                    const done = totalStars >= m.stars;
                    const colors = ["#FFD700","#4ECDC4","#FF6B9D","#7B2FBE","#FF6B6B"];
                    return (
                      <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", borderBottom: i < milestones.length - 1 ? `1px solid ${T.navBorder}` : "none", opacity: done ? 1 : 0.65 }}>
                        <div style={{ width: 36, height: 36, borderRadius: "50%", background: done ? colors[i % colors.length] : T.navBorder, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, flexShrink: 0 }}>{done ? "✅" : "🔒"}</div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 700, fontSize: 14 }}>
                            <input className="milestone-input" value={m.reward} onChange={e => handleMilestoneChange(i, "reward", e.target.value)} placeholder="Enter reward title..." />
                          </div>
                          <div style={{ fontSize: 12, color: T.subtext, display: "flex", alignItems: "center", gap: 4 }}>
                            <input className="milestone-input" type="number" value={m.stars} onChange={e => handleMilestoneChange(i, "stars", e.target.value)} style={{ width: 50, textAlign: "center", background: "rgba(0,0,0,0.03)", borderRadius: 4 }} /> stars required
                          </div>
                        </div>
                        {done && <div style={{ fontSize: 11, fontWeight: 800, color: colors[i % colors.length], flexShrink: 0 }}>EARNED!</div>}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* ══ VIEW: CONFIG & MANAGE HABITS ══ */}
            {page === "manage" && (
              <div>
                <div style={{ textAlign: "center", marginBottom: 20 }}>
                  <div style={{ fontSize: 40 }}>⚙️</div>
                  <div style={{ fontSize: 24, fontWeight: 900, color: T.primary }}>Manage Habits</div>
                </div>
                <div style={{ background: T.card, borderRadius: 20, padding: 16, boxShadow: T.shadow, marginBottom: 16 }}>
                  <div style={{ fontWeight: 800, marginBottom: 8 }}>👶 Child's Name</div>
                  <input value={childName} onChange={e => saveName(e.target.value)} placeholder="Enter name..." style={{ width: "100%", padding: "10px 14px", borderRadius: 12, border: `2px solid ${T.navBorder}`, fontFamily: T.font, fontSize: 15, fontWeight: 700, color: T.text, background: T.navBg, outline: "none", boxSizing: "border-box" }} />
                </div>
                <div style={{ background: T.card, borderRadius: 20, padding: 16, boxShadow: T.shadow, marginBottom: 16 }}>
                  <div style={{ fontWeight: 800, marginBottom: 10 }}>➕ Add Habit</div>
                  <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
                    <input value={newHabitEmoji} onChange={e => setNewHabitEmoji(e.target.value)} style={{ width: 58, padding: "9px", borderRadius: 12, textAlign: "center", border: `2px solid ${T.navBorder}`, fontSize: 20, background: T.navBg, color: T.text, outline: "none", fontFamily: T.font }} />
                    <input value={newHabitName} onChange={e => setNewHabitName(e.target.value)} placeholder="Habit name..." onKeyDown={e => { if (e.key === "Enter" && newHabitName.trim()) { saveHabits([...habits, { id: Date.now(), name: newHabitName.trim(), emoji: newHabitEmoji || "⭐", active: true, stars: 0 }]); setNewHabitName(""); setNewHabitEmoji("⭐"); } }} style={{ flex: 1, padding: "9px 12px", borderRadius: 12, border: `2px solid ${T.navBorder}`, fontSize: 14, fontFamily: T.font, background: T.navBg, color: T.text, outline: "none" }} />
                  </div>
                  <button onClick={() => { if (!newHabitName.trim()) return; saveHabits([...habits, { id: Date.now(), name: newHabitName.trim(), emoji: newHabitEmoji || "⭐", active: true, stars: 0 }]); setNewHabitName(""); setNewHabitEmoji("⭐"); }} style={{ width: "100%", padding: "11px", background: `linear-gradient(135deg, ${T.primary}, ${T.secondary})`, border: "none", borderRadius: 12, color: "#fff", fontWeight: 800, fontSize: 14, cursor: "pointer", fontFamily: T.font }}>Add Habit</button>
                </div>
                <div style={{ background: T.card, borderRadius: 20, padding: 16, boxShadow: T.shadow }}>
                  <div style={{ fontWeight: 800, marginBottom: 12 }}>📋 Habits ({habits.length})</div>
                  {habits.map(h => (
                    <div key={h.id} style={{ borderBottom: `1px solid ${T.navBorder}`, paddingBottom: 12, marginBottom: 12 }}>
                      {editingId === h.id ? (
                        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                          <input value={editEmoji} onChange={e => setEditEmoji(e.target.value)} style={{ width: 50, padding: "7px", borderRadius: 10, textAlign: "center", border: `2px solid ${T.primary}`, fontSize: 18, fontFamily: T.font, background: T.navBg, color: T.text, outline: "none" }} />
                          <input value={editName} onChange={e => setEditName(e.target.value)} style={{ flex: 1, padding: "7px 10px", borderRadius: 10, border: `2px solid ${T.primary}`, fontSize: 13, fontFamily: T.font, background: T.navBg, color: T.text, outline: "none" }} />
                          <button onClick={() => { saveHabits(habits.map(x => x.id === h.id ? { ...x, name: editName, emoji: editEmoji } : x)); setEditingId(null); }} style={{ background: T.secondary, border: "none", borderRadius: 8, padding: "7px 11px", color: "#fff", fontWeight: 700, cursor: "pointer" }}>✓</button>
                          <button onClick={() => setEditingId(null)} style={{ background: T.subtext, border: "none", borderRadius: 8, padding: "7px 9px", color: "#fff", fontWeight: 700, cursor: "pointer" }}>✕</button>
                        </div>
                      ) : (
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <span style={{ fontSize: 26 }}>{h.emoji}</span>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontWeight: 700, fontSize: 14, color: h.active ? T.text : T.subtext, textDecoration: h.active ? "none" : "line-through" }}>{h.name}</div>
                            <div style={{ fontSize: 11, color: T.subtext }}>{h.stars} ⭐ earned</div>
                          </div>
                          <button onClick={() => saveHabits(habits.map(x => x.id === h.id ? { ...x, active: !x.active } : x))} style={{ padding: "4px 9px", borderRadius: 20, border: "none", background: h.active ? T.secondary + "33" : T.navBorder, color: h.active ? T.secondary : T.subtext, fontSize: 11, fontWeight: 800, cursor: "pointer", fontFamily: T.font }}>{h.active ? "ON" : "OFF"}</button>
                          <button onClick={() => { setEditingId(h.id); setEditName(h.name); setEditEmoji(h.emoji); }} style={{ width: 30, height: 30, borderRadius: 8, border: "none", background: T.navBorder, cursor: "pointer", fontSize: 14 }}>✏️</button>
                          <button onClick={() => saveHabits(habits.filter(x => x.id !== h.id))} style={{ width: 30, height: 30, borderRadius: 8, border: "none", background: "#ffebee", cursor: "pointer", fontSize: 14 }}>🗑️</button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      );
    }

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>
"""

# Dynamic context placeholder variables injections
html_code = html_code.replace("INITIAL_HABITS_PLACEHOLDER", json.dumps(cloud_habits))
html_code = html_code.replace("INITIAL_STARS_PLACEHOLDER", json.dumps(cloud_stars))
# FIXED: Safe serialization for child_name string placeholder to avoid token breakdown
html_code = html_code.replace("INITIAL_NAME_PLACEHOLDER", json.dumps(cloud_name))

# FIXED: Strict absolute path generation for rock-solid workspace tracking across deployments
PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
COMPONENT_DIR = os.path.join(PARENT_DIR, "tracker_frontend")

if not os.path.exists(COMPONENT_DIR):
    os.makedirs(COMPONENT_DIR)
    
with open(os.path.join(COMPONENT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(html_code)

# Compile standard two-way connection listener
star_tracker_component = components.declare_component("star_tracker_component", path=COMPONENT_DIR)

# Render active layout frame and accept incoming save-state updates from React
component_data = star_tracker_component(key="main_tracker")

# 4. INSTANT BACKEND DISK SYNCHRONIZATION EVENT LISTENER
if component_data:
    incoming_stars = component_data.get("stars", [])
    incoming_habits = component_data.get("habits", [])
    incoming_name = component_data.get("child_name", "My Star!")
    
    # FIXED: Generate a robust MD5 hash fingerprint of the actual data contents to accurately catch any internal changes
    state_payload = {"stars": incoming_stars, "habits": incoming_habits, "child_name": incoming_name}
    state_fingerprint = hashlib.md5(json.dumps(state_payload, sort_keys=True).encode()).hexdigest()
    
    if state_fingerprint != st.session_state.get("last_state_fingerprint"):
        st.session_state["last_state_fingerprint"] = state_fingerprint
        
        if conn is not None:
            try:
                conn.update(worksheet="Habits", data=pd.DataFrame(incoming_habits))
                conn.update(worksheet="Stars", data=pd.DataFrame(incoming_stars))
                conn.update(worksheet="Settings", data=pd.DataFrame([{"child_name": incoming_name}]))
            except Exception:
                pass
        st.rerun()
