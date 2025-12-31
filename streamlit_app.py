import streamlit as st
import os
import time
import datetime
import sqlite3
import json
import base64
import io
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr

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
    .orb.speaking { background: #ec4899; box-shadow: 0 0 100px rgba(236, 72, 153, 0.5); transform: scale(1.1); }
    
    @keyframes pulse { from { transform: scale(1); } to { transform: scale(1.1); } }
    
    .status { text-align: center; color: #818cf8; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 20px; font-size: 1rem; }
    .chat-card { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #333; }
    
    .stButton > button { border-radius: 20px; padding: 15px; font-weight: 700; background: #6366f1 !important; color: white !important; width: 100%; transition: 0.3s; }
    .stop-btn button { background: #111 !important; color: #ef4444 !important; border: 1px solid #ef4444 !important; }
    
    #MainMenu, footer {visibility: hidden;}
    .synapse-header { color: #818cf8; border-bottom: 1px solid #1a1a2e; padding-bottom: 10px; margin-bottom: 20px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }

    /* Stealth Mic Button: Hide it but leave it clickable for JS */
    div[data-testid="stVerticalBlock"] div[data-testid="stMarkdownContainer"] + div button:has(div:contains("🎙️")) {
        opacity: 0;
        height: 1px;
        width: 1px;
        position: absolute;
        top: -100px;
    }
</style>
""", unsafe_allow_html=True)

# Logo
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

# --- BI-DIRECTIONAL VOICE ENGINE (JS) ---
def trigger_voice_and_auto_listen():
    gender = v_identity.lower()
    payload = st.session_state.speak_text if st.session_state.speak_text else ""
    
    js_code = f"""
        <script>
            var isActive = {json.dumps(st.session_state.active)};
            var speakText = {json.dumps(payload)};
            var gender = "{gender}";

            function autoClickMic() {{
                const buttons = window.parent.document.querySelectorAll('button');
                for (let btn of buttons) {{
                    if (btn.innerText.includes('🎙️')) {{
                        btn.click();
                        break;
                    }}
                }}
            }}

            function runAura() {{
                if (!isActive) return;

                if (speakText) {{
                    window.speechSynthesis.cancel();
                    var msg = new SpeechSynthesisUtterance(speakText);
                    var voices = window.speechSynthesis.getVoices();
                    var target = voices.find(v => {{
                        var n = v.name.toLowerCase();
                        if (gender === 'female') return n.includes('female') || n.includes('zira') || n.includes('aria') || n.includes('samantha') || n.includes('linda');
                        return n.includes('male') || n.includes('david') || n.includes('alex') || n.includes('guy');
                    }});
                    msg.voice = target || voices[0];
                    msg.rate = 1.1;
                    msg.onend = function() {{
                        // Once Aura is done speaking, click the mic to listen again
                        setTimeout(autoClickMic, 400);
                    }};
                    window.speechSynthesis.speak(msg);
                }} else {{
                    // Initial listen if no speak text
                    setTimeout(autoClickMic, 500);
                }}
            }}

            if (window.speechSynthesis.onvoiceschanged !== undefined) {{
                window.speechSynthesis.onvoiceschanged = runAura;
            }}
            setTimeout(runAura, 800);
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
status_label = "AURA IS READY" if st.session_state.active else "SYSTEM OFFLINE"

if st.session_state.speak_text:
    orb_class = "speaking"
    status_label = "AURA IS RESPONDING"

orb_placeholder.markdown(f'<div class="orb-box"><div class="orb {orb_class}"></div></div>', unsafe_allow_html=True)
status_placeholder.markdown(f'<div class="status">{status_label}</div>', unsafe_allow_html=True)

# --- STEALTH MIC RECORDER (Hidden) ---
# This serves as the hardware interface for both Local and Cloud
st.markdown('<div style="display:none;">', unsafe_allow_html=True)
audio_input = mic_recorder(
    start_prompt="🎙️",
    stop_prompt="🛑",
    just_once=True,
    format="wav",
    key='aura_supreme_mic'
)
st.markdown('</div>', unsafe_allow_html=True)

# --- BRAIN PROCESSING ---
if audio_input and st.session_state.active:
    audio_bytes = audio_input['bytes']
    if audio_bytes:
        try:
            r = sr.Recognizer()
            audio_stream = io.BytesIO(audio_bytes)
            with sr.AudioFile(audio_stream) as source:
                r.adjust_for_ambient_noise(source, duration=0.2)
                audio_data = r.record(source)
            
            transcript = r.recognize_google(audio_data)
            if transcript:
                st.session_state.history.append({"role": "user", "text": transcript})
                
                client = Groq(api_key=api_key)
                msgs = [{"role": "system", "content": "You are Aura. Be concise, fast, and natural like Alexa. You remember history."}]
                for turn in st.session_state.history[-8:]:
                    msgs.append({"role": "user" if turn['role']=='user' else "assistant", "content": turn['text']})
                
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, max_tokens=150)
                answer = res.choices[0].message.content
                
                save_to_db(transcript, answer)
                st.session_state.history.append({"role": "bot", "text": answer})
                st.session_state.speak_text = answer
                st.rerun()
        except:
            # Silent retry if no words found
            st.rerun()

# Trigger the Loop
if st.session_state.active:
    trigger_voice_and_auto_listen()
    st.session_state.speak_text = None

# --- HISTORY DISPLAY (Newest First) ---
if st.session_state.history:
    st.divider()
    st.markdown('<div class="synapse-header">🧬 ACTIVE SYNAPSES</div>', unsafe_allow_html=True)
    for m in reversed(st.session_state.history[-6:]):
        color = "#6366f1" if m['role'] == 'user' else "#ec4899"
        role_label = "👤 YOU" if m['role'] == 'user' else "✨ AURA"
        st.markdown(f"""
            <div class="chat-card" style="border-left: 4px solid {color}; shadow: 0 4px 12px rgba(0,0,0,0.5);">
                <b style="color:{color}; letter-spacing: 1px;">{role_label}</b><br>
                <span style="font-size: 1.1rem; line-height: 1.6;">{m["text"]}</span>
            </div>
        """, unsafe_allow_html=True)

# Vault display
if vault_toggle:
    st.divider()
    st.markdown('<div class="synapse-header">🏛️ NEURAL VAULT</div>', unsafe_allow_html=True)
    vault = get_vault_data()
    for entry in vault:
        with st.expander(f"📍 {entry[0]} | {entry[1][:30]}..."):
            st.write(f"**Human:** {entry[1]}")
            st.write(f"**Aura:** {entry[2]}")
