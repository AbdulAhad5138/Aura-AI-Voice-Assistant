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
st.set_page_config(page_title="AURA AI | Supreme Alexa", page_icon="🤖", layout="wide")

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
    .orb { width: 140px; height: 140px; border-radius: 50%; background: #050505; border: 1px solid #111; transition: 0.5s; position: relative; }
    .orb.active { background: #6366f1; box-shadow: 0 0 80px rgba(99, 102, 241, 0.4); animation: pulse 1.5s infinite alternate; }
    .orb.speaking { background: #ec4899; box-shadow: 0 0 80px rgba(236, 72, 153, 0.5); transform: scale(1.1); }
    @keyframes pulse { from { transform: scale(1); } to { transform: scale(1.1); } }
    .status { text-align: center; color: #818cf8; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 20px; font-size: 0.9rem; }
    .chat-card { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; margin-bottom: 10px; }
    .stButton > button { border-radius: 20px; padding: 12px; font-weight: 700; background: #6366f1 !important; color: white !important; width: 100%; }
    .stop-btn button { background: #000 !important; color: #ef4444 !important; border: 1px solid #ef4444 !important; }
    #MainMenu, footer {visibility: hidden;}
    
    /* Hide the technical chat input used as a proxy */
    div[data-testid="stChatInput"] { position: fixed; bottom: -100px; }
</style>
""", unsafe_allow_html=True)

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
        st.rerun()

# --- THE SUPREME BRIDGE ---
# We use st.chat_input as a hidden listener for the JS Bridge
user_voice_text = st.chat_input("Listening...")

# If JS sent back a transcription via chat_input
if user_voice_text:
    st.session_state.history.append({"role": "user", "text": user_voice_text})
    
    # Brain Phase
    client = Groq(api_key=api_key)
    msgs = [{"role": "system", "content": "You are Aura. Be concise like Alexa. You remember history."}]
    for turn in st.session_state.history[-6:]:
        msgs.append({"role": "user" if turn['role']=='user' else "assistant", "content": turn['text']})
    
    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, max_tokens=150)
    ans = res.choices[0].message.content
    
    save_to_db(user_voice_text, ans)
    st.session_state.history.append({"role": "bot", "text": ans})
    st.rerun()

# Phase Management
orb_class = ""
status_label = "OFFLINE"
speak_payload = ""

if st.session_state.active:
    orb_class = "active"
    status_label = "LISTENING..."
    if st.session_state.history and st.session_state.history[-1]['role'] == 'bot':
        speak_payload = st.session_state.history[-1]['text']
        orb_class = "speaking"
        status_label = "AURA IS RESPONDING"

# --- THE BRAIN BRIDGE (JS) ---
def trigger_neural_bridge():
    gender = v_identity.lower()
    active_flag = "true" if st.session_state.active else "false"
    
    js_code = f"""
        <script>
            var active = {active_flag};
            var speakText = {json.dumps(speak_payload)};
            var gender = "{gender}";

            function bridgeToStreamlit(text) {{
                const input = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
                if (input) {{
                    input.value = text;
                    const event = new Event('input', {{ bubbles: true }});
                    input.dispatchEvent(event);
                    
                    // Simulate Enter key
                    const keyboardEvent = new KeyboardEvent('keydown', {{
                        key: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true
                    }});
                    input.dispatchEvent(keyboardEvent);
                }}
            }}

            function startSpeech() {{
                if (!active) return;
                
                if (speakText) {{
                    window.speechSynthesis.cancel();
                    const msg = new SpeechSynthesisUtterance(speakText);
                    const voices = window.speechSynthesis.getVoices();
                    const target = voices.find(v => {{
                        const n = v.name.toLowerCase();
                        if (gender === 'female') return n.includes('female') || n.includes('zira') || n.includes('aria') || n.includes('samantha');
                        return n.includes('male') || n.includes('david') || n.includes('alex');
                    }});
                    msg.voice = target || voices[0];
                    msg.rate = 1.05;
                    msg.onend = function() {{
                        // Automatically restart listening after speaking finishes
                        setTimeout(listen, 300);
                    }};
                    window.speechSynthesis.speak(msg);
                }} else {{
                    listen();
                }}
            }}

            function listen() {{
                if (!active) return;
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) return;
                
                const rec = new SpeechRecognition();
                rec.lang = 'en-US';
                rec.continuous = false; // "false" triggers silence detection automatically!
                rec.interimResults = false;

                rec.onresult = (e) => {{
                    const transcript = e.results[0][0].transcript;
                    bridgeToStreamlit(transcript);
                }};

                rec.onerror = (e) => {{
                    if (active) setTimeout(listen, 1000);
                }};

                rec.onend = () => {{
                    // If it ended naturally without result (no speech), just restart
                }};

                rec.start();
            }}

            if (window.speechSynthesis.onvoiceschanged !== undefined) {{
                window.speechSynthesis.onvoiceschanged = startSpeech;
            }}
            setTimeout(startSpeech, 500);
        </script>
    """
    st.components.v1.html(js_code, height=0)

# --- UI CONTROLS ---
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if not st.session_state.active:
        if st.button("🔌 START NEURAL LINK"):
            st.session_state.active = True
            st.rerun()
    else:
        st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
        if st.button("🛑 DISCONNECT LINK"):
            st.session_state.active = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f'<div class="orb-box"><div class="orb {orb_class}"></div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="status">{status_label}</div>', unsafe_allow_html=True)

if st.session_state.active:
    trigger_neural_bridge()

# History
if vault_toggle:
    st.divider(); st.markdown("### 🏛️ NEURAL VAULT")
    vault = get_vault_data()
    for entry in vault:
        with st.expander(f"📍 {entry[0]} | {entry[1][:25]}..."):
            st.write(f"**Human:** {entry[1]} "); st.write(f"**Aura:** {entry[2]}")

if st.session_state.history:
    st.divider(); st.markdown("### 🧬 ACTIVE SYNAPSES")
    for m in reversed(st.session_state.history[-4:]):
        color = "#6366f1" if m['role'] == 'user' else "#ec4899"
        name = "👤 YOU" if m['role'] == 'user' else "✨ AURA"
        st.markdown(f'<div class="chat-card"><b style="color:{color};">{name}</b><br>{m["text"]}</div>', unsafe_allow_html=True)
