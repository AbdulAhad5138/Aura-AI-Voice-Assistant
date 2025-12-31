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
st.set_page_config(page_title="AURA AI | Alexa Infinite", page_icon="🤖", layout="wide")

# Persistent Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "aura_data"
DATA_DIR.mkdir(exist_ok=True, parents=True)
DB_PATH = DATA_DIR / "aura_vault.db"
LOGO_PATH = DATA_DIR / "logo.png"

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

db_healthy = init_db()

# Session States
if 'history' not in st.session_state: st.session_state.history = []
if 'speak_text' not in st.session_state: st.session_state.speak_text = None
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
    
    .stButton > button { border-radius: 20px; padding: 12px; font-weight: 700; background: #6366f1 !important; color: white !important; width: 100%; transition: 0.3s; }
    .stop-btn button { background: #000 !important; color: #ef4444 !important; border: 1px solid #ef4444 !important; }
    #MainMenu, footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Helper for Logo
def get_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

if LOGO_PATH.exists():
    logo_b64 = get_image_base64(LOGO_PATH)
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
        st.rerun()
    st.write(f"DB Node: {'🟢 ONLINE' if db_healthy else '🔴 ERROR'}")

# --- ALEXA BRIDGE (TRANSCRIPTION + VOICE ENGINE) ---
# This script handles browser-side audio, sends it to st.session_state, and plays voice
def alexa_bridge():
    # We use a custom HTML component that uses Web Speech API for both recognition and synthesis
    # to achieve the true hands-to-free loop.
    js_code = f"""
        <script>
            var active = {json.dumps(st.session_state.active)};
            var last_text = {json.dumps(st.session_state.speak_text)};
            var gender = {json.dumps(v_identity.lower())};
            
            if (active) {{
                // 🔊 VOICE OUTPUT
                if (last_text) {{
                    window.speechSynthesis.cancel();
                    var msg = new SpeechSynthesisUtterance(last_text);
                    var voices = window.speechSynthesis.getVoices();
                    var targetVoice = voices.find(v => {{
                        var n = v.name.toLowerCase();
                        if (gender === 'female') return n.includes('female') || n.includes('zira') || n.includes('aria') || n.includes('samantha');
                        return n.includes('male') || n.includes('david') || n.includes('alex');
                    }});
                    msg.voice = targetVoice || voices[0];
                    msg.rate = 1.05;
                    msg.onend = function() {{
                        // Automatically start listening after speaking is done
                        startListening();
                    }};
                    window.speechSynthesis.speak(msg);
                }} else {{
                    startListening();
                }}

                function startListening() {{
                    var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                    recognition.lang = 'en-US';
                    recognition.interimResults = false;
                    recognition.maxAlternatives = 1;

                    recognition.onresult = function(event) {{
                        var txt = event.results[0][0].transcript;
                        // Send text to Streamlit
                        const data = {{type: 'transcription', text: txt}};
                        window.parent.postMessage({{type: 'streamlit:setComponentValue', value: data}}, '*');
                    }};

                    recognition.onerror = function(event) {{
                        // Silent retry if no audio detected
                        setTimeout(startListening, 500);
                    }};

                    recognition.start();
                }}
            }}
        </script>
    """
    # This component captures the return data from the JS
    result = st.components.v1.html(js_code, height=0)
    return result

# --- MAIN LOOP ---
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
            st.session_state.speak_text = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Orb Logic
orb_style = "active" if st.session_state.active else ""
status_label = "READY" if st.session_state.active else "OFFLINE"
if st.session_state.speak_text:
    orb_style = "speaking"
    status_label = "AURA IS RESPONDING"

st.markdown(f'<div class="orb-box"><div class="orb {orb_style}"></div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="status">{status_label}</div>', unsafe_allow_html=True)

# --- THE HIDDEN BRIDGE ---
# We use st.chat_input as a hidden proxy for the JS bridge data
if st.session_state.active:
    # Trigger the JS Bridge
    alexa_bridge()

# Catch data from the browser (JS sends transcription)
# Since we can't easily catch JS messages directly in one turn, 
# we've optimized the app to capture voice data via standard mic_recorder 
# but we will simulate the Alexa loop by re-triggering.

# FOR BEST CLOUD COMPATIBILITY: We use the mic_recorder as the trigger 
# but hide it in a way that feels automatic.
from streamlit_mic_recorder import mic_recorder

st.markdown('<div style="display:flex; justify-content:center; margin-bottom:20px;">', unsafe_allow_html=True)
audio = mic_recorder(
    start_prompt="🎙️ PUSH TO START ALEXA LOOP",
    stop_prompt="🛑 STOP",
    just_once=True,
    format="wav",
    key='alexa_mic'
)
st.markdown('</div>', unsafe_allow_html=True)

if audio:
    import io
    import speech_recognition as sr
    audio_bytes = audio['bytes']
    if audio_bytes:
        r = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            r.adjust_for_ambient_noise(source)
            audio_data = r.record(source)
        try:
            user_text = r.recognize_google(audio_data)
            st.session_state.history.append({"role": "user", "text": user_text})
            
            # Brain
            client = Groq(api_key=api_key)
            msgs = [{"role": "system", "content": "You are Aura. Be concise like Alexa. You remember everything."}]
            for turn in st.session_state.history[-6:]:
                msgs.append({"role": "user" if turn['role']=='user' else "assistant", "content": turn['text']})
            
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, max_tokens=150)
            ans = res.choices[0].message.content
            
            save_to_db(user_text, ans)
            st.session_state.history.append({"role": "bot", "text": ans})
            st.session_state.speak_text = ans
            st.rerun()
        except: pass

# Trigger Voice JS
if st.session_state.speak_text:
    gender = v_identity.lower()
    js_speak = f"""
        <script>
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance({json.dumps(st.session_state.speak_text)});
            var voices = window.speechSynthesis.getVoices();
            var targetVoice = voices.find(v => {{
                var n = v.name.toLowerCase();
                if ('{gender}' === 'female') return n.includes('female') || n.includes('zira') || n.includes('aria');
                return n.includes('male') || n.includes('david');
            }});
            msg.voice = targetVoice || voices[0];
            window.speechSynthesis.speak(msg);
        </script>
    """
    st.components.v1.html(js_speak, height=0)
    st.session_state.speak_text = None

# History Vault
if vault_toggle:
    st.divider(); st.markdown("### 🏛️ NEURAL VAULT")
    vault = get_vault_data()
    for entry in vault:
        with st.expander(f"📍 {entry[0]} | {entry[1][:25]}..."):
            st.write(f"**Human:** {entry[1]}"); st.write(f"**Aura:** {entry[2]}")

if st.session_state.history:
    st.divider(); st.markdown("### 🧬 ACTIVE SYNAPSES")
    for m in reversed(st.session_state.history[-4:]):
        color = "#6366f1" if m['role'] == 'user' else "#ec4899"
        name = "👤 YOU" if m['role'] == 'user' else "✨ AURA"
        st.markdown(f'<div class="chat-card"><b style="color:{color};">{name}</b><br>{m["text"]}</div>', unsafe_allow_html=True)
