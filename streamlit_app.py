import streamlit as st
import os
import time
import datetime
import sqlite3
import json
import base64
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

# Load Environment
load_dotenv()

# --- INITIALIZATION ---
st.set_page_config(page_title="AURA AI | Pure Voice Alexa", page_icon="🤖", layout="wide")

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "aura_data"
DATA_DIR.mkdir(exist_ok=True, parents=True)
DB_PATH = DATA_DIR / "aura_vault.db"
LOGO_PATH = BASE_DIR / "assets" / "logo.png"

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS conversation_vault
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      timestamp TEXT, 
                      user_query TEXT, 
                      bot_response TEXT)''')
        conn.commit()
        conn.close()
        return True
    except: return False

def save_to_db(query, response):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO conversation_vault (timestamp, user_query, bot_response) VALUES (?, ?, ?)",
                  (ts, query, response))
        conn.commit()
        conn.close()
    except: pass

def get_vault_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT timestamp, user_query, bot_response FROM conversation_vault ORDER BY id DESC LIMIT 50")
        rows = c.fetchall()
        conn.close()
        return rows
    except: return []

init_db()

# Session States
if 'history' not in st.session_state: st.session_state.history = []
if 'active' not in st.session_state: st.session_state.active = False
if 'speak_text' not in st.session_state: st.session_state.speak_text = None

# API Key
api_key = os.getenv("GROQ_API_KEY", "")

# --- LUXURY STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=Space+Grotesk:wght@600&display=swap');
    .stApp { background: #020205; color: #f8fafc; font-family: 'Outfit', sans-serif; }
    
    .logo-container { text-align: center; padding-top: 10px; }
    .logo-img { width: 110px; margin: 0 auto; display: block; animation: float 4s infinite ease-in-out; }
    @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }

    .title { font-family: 'Space Grotesk', sans-serif; font-size: 4rem; text-align: center; background: linear-gradient(180deg, #fff 0%, #475569 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; letter-spacing: -4px; }
    
    .orb-box { display: flex; justify-content: center; margin: 20px 0; }
    .orb { width: 150px; height: 150px; border-radius: 50%; background: #050505; border: 1px solid #111; transition: 0.5s; position: relative; }
    .orb.active { background: #6366f1; box-shadow: 0 0 100px rgba(99, 102, 241, 0.4); animation: pulse 1.5s infinite alternate; }
    .orb.thinking { background: #a855f7; box-shadow: 0 0 100px rgba(168, 85, 247, 0.4); animation: pulse 1s infinite alternate; }
    .orb.speaking { background: #ec4899; box-shadow: 0 0 100px rgba(236, 72, 153, 0.5); transform: scale(1.1); }
    
    @keyframes pulse { from { transform: scale(1); } to { transform: scale(1.1); } }
    
    .status { text-align: center; color: #818cf8; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 20px; font-size: 1rem; }
    .chat-card { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #333; }
    
    .stButton > button { border-radius: 20px; padding: 15px; font-weight: 700; background: #6366f1 !important; color: white !important; width: 100%; transition: 0.3s; }
    .stop-btn button { background: #111 !important; color: #ef4444 !important; border: 1px solid #ef4444 !important; }
    
    #MainMenu, footer {visibility: hidden;}
    .synapse-header { color: #818cf8; border-bottom: 1px solid #1a1a2e; padding-bottom: 10px; margin-bottom: 20px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }

    /* ABSOLUTELY HIDE TEXT CHAT INPUT */
    div[data-testid="stChatInput"] { 
        display: none !important; 
        visibility: hidden !important; 
        pointer-events: none !important;
        position: fixed;
        bottom: -500px;
    }
</style>
""", unsafe_allow_html=True)

# Header
if LOGO_PATH.exists():
    with open(LOGO_PATH, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    st.markdown(f'<div class="logo-container"><img src="data:image/png;base64,{logo_b64}" class="logo-img"></div>', unsafe_allow_html=True)
st.markdown(f'<h1 class="title">AURA</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ SYSTEM CONTROL")
    v_identity = st.radio("VOICE IDENTITY", ["Female", "Male"])
    st.divider()
    vault_toggle = st.toggle("Open Neural Vault", value=False)
    if st.button("Purge Session"):
        st.session_state.history = []
        st.session_state.active = False
        st.session_state.speak_text = None
        st.rerun()

# --- THE PURE VOICE BRIDGE (NO TEXT INPUTS VISIBLE) ---
def voice_bridge():
    gender = v_identity.lower()
    payload = st.session_state.speak_text if st.session_state.speak_text else ""
    
    js_code = f"""
        <script>
            var isActive = {json.dumps(st.session_state.active)};
            var speakText = {json.dumps(payload)};
            var gender = "{gender}";

            // Bridge to send transcript back via hidden proxy
            function sendTranscript(text) {{
                const input = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
                if (input) {{
                    input.value = text;
                    const event = new Event('input', {{ bubbles: true }});
                    input.dispatchEvent(event);
                    const enterEvent = new KeyboardEvent('keydown', {{
                        key: 'Enter', keyCode: 13, which: 13, bubbles: true
                    }});
                    input.dispatchEvent(enterEvent);
                }}
            }}

            function startAuraLoop() {{
                if (!isActive) return;

                if (speakText) {{
                    // TALK
                    window.speechSynthesis.cancel();
                    var msg = new SpeechSynthesisUtterance(speakText);
                    var voices = window.speechSynthesis.getVoices();
                    var target = voices.find(v => {{
                        var n = v.name.toLowerCase();
                        if (gender === 'female') return n.includes('female') || n.includes('zira') || n.includes('aria') || n.includes('samantha');
                        return n.includes('male') || n.includes('david') || n.includes('alex') || n.includes('guy');
                    }});
                    msg.voice = target || voices[0];
                    msg.rate = 1.1;
                    msg.onend = function() {{
                        // Alexa Loop: Listen immediately after speaking
                        setTimeout(listenNow, 300);
                    }};
                    window.speechSynthesis.speak(msg);
                }} else {{
                    // LISTEN (Initial)
                    listenNow();
                }}
            }}

            function listenNow() {{
                if (!isActive) return;
                var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) return;

                var r = new SpeechRecognition();
                r.lang = 'en-US';
                r.continuous = false;
                r.interimResults = false;

                r.onresult = function(e) {{
                    var transcript = e.results[0][0].transcript;
                    sendTranscript(transcript);
                }};

                r.onerror = function(e) {{
                    if (isActive) {{
                        if (e.error === 'not-allowed') {{
                             console.error("Mic Permission Denied.");
                        }} else {{
                             setTimeout(listenNow, 800);
                        }}
                    }}
                }};

                r.start();
            }}

            // Start logic
            if (window.speechSynthesis.onvoiceschanged !== undefined) {{
                window.speechSynthesis.onvoiceschanged = startAuraLoop;
            }}
            setTimeout(startAuraLoop, 800);
        </script>
    """
    st.components.v1.html(js_code, height=0)

# Connect Button
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if not st.session_state.active:
        if st.button("🔌LETS START "):
            st.session_state.active = True
            st.rerun()
    else:
        st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
        if st.button("🛑 DISCONNECT LINK"):
            st.session_state.active = False
            st.session_state.speak_text = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Status & Orb
orb_placeholder = st.empty()
status_placeholder = st.empty()

orb_class = "active" if st.session_state.active else ""
status_label = "AURA IS READY & LISTENING..." if st.session_state.active else "SYSTEM OFFLINE"

if st.session_state.speak_text:
    orb_class = "speaking"
    status_label = "AURA IS RESPONDING"

orb_placeholder.markdown(f'<div class="orb-box"><div class="orb {orb_class}"></div></div>', unsafe_allow_html=True)
status_placeholder.markdown(f'<div class="status">{status_label}</div>', unsafe_allow_html=True)

# THE HIDDEN BRIDGE (PROXY)
# This is fully hidden by the CSS above but receives data from the voice bridge
transcript_input = st.chat_input("Speak...")

if transcript_input and st.session_state.active:
    # Brain Phase
    st.session_state.history.append({"role": "user", "text": transcript_input})
    
    client = Groq(api_key=api_key)
    msgs = [{"role": "system", "content": "You are Aura. Be concise, fast, and natural like Alexa. NEVER mention being a chatbot."}]
    for turn in st.session_state.history[-8:]:
        msgs.append({"role": "user" if turn['role']=='user' else "assistant", "content": turn['text']})
    
    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, max_tokens=150)
    answer = res.choices[0].message.content
    
    save_to_db(transcript_input, answer)
    st.session_state.history.append({"role": "bot", "text": answer})
    st.session_state.speak_text = answer
    st.rerun()

# Trigger Neural Bridge
if st.session_state.active:
    voice_bridge()
    st.session_state.speak_text = None

# --- HISTORY DISPLAY (Newest First) ---
if st.session_state.history:
    st.divider()
    st.markdown('<div class="synapse-header">🧬 ACTIVE SYNAPSES</div>', unsafe_allow_html=True)
    for m in reversed(st.session_state.history[-6:]):
        color = "#6366f1" if m['role'] == 'user' else "#ec4899"
        role_label = "👤 YOU" if m['role'] == 'user' else "✨ AURA"
        st.markdown(f"""
            <div class="chat-card" style="border-left: 4px solid {color};">
                <b style="color:{color}; letter-spacing: 1px;">{role_label}</b><br>
                <span style="font-size: 1.1rem; line-height: 1.6;">{m["text"]}</span>
            </div>
        """, unsafe_allow_html=True)

# Vault
if vault_toggle:
    st.divider()
    st.markdown('<div class="synapse-header">🏛️ NEURAL VAULT</div>', unsafe_allow_html=True)
    vault = get_vault_data()
    for entry in vault:
        with st.expander(f"📍 {entry[0]} | {entry[1][:30]}..."):
            st.write(f"**Human:** {entry[1]}")
            st.write(f"**Aura:** {entry[2]}")
