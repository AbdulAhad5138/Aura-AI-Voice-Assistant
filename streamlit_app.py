import streamlit as st
import speech_recognition as sr
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

# Load Environment
load_dotenv()

# --- INITIALIZATION ---
st.set_page_config(page_title="AURA AI | Ultra-Smooth", page_icon="🤖", layout="wide")

# Paths for Stability
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
    except Exception:
        return False

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
if 'speak_text' not in st.session_state: st.session_state.speak_text = None
api_key_system = os.getenv("GROQ_API_KEY", "")

# --- LUXURY STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=Space+Grotesk:wght@600&display=swap');
    .stApp { background: #020205; color: #f8fafc; font-family: 'Outfit', sans-serif; }
    
    .title-container { text-align: center; padding-top: 10px; }
    .title { font-family: 'Space Grotesk', sans-serif; font-size: 4.5rem; background: linear-gradient(180deg, #fff 0%, #475569 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; letter-spacing: -4px; }
    
    .logo-img { width: 120px; margin: 0 auto; display: block; animation: float 4s infinite ease-in-out; }
    @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }

    .orb-box { display: flex; justify-content: center; margin: 10px 0; }
    .orb { width: 150px; height: 150px; border-radius: 50%; background: #0a0a0f; border: 1px solid #1a1a2e; transition: 0.5s; }
    .orb.active { background: #6366f1; box-shadow: 0 0 80px rgba(99, 102, 241, 0.4); animation: pulse 1.5s infinite alternate; }
    .orb.speaking { background: #ec4899; box-shadow: 0 0 80px rgba(236, 72, 153, 0.5); transform: scale(1.1); }
    
    @keyframes pulse { from { transform: scale(1); } to { transform: scale(1.1); } }
    
    .status { text-align: center; color: #818cf8; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 20px; font-size: 0.9rem; }
    .chat-card { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; margin-bottom: 10px; font-size: 0.95rem; }
    
    /* Center the mic recorder */
    .mic-container { display: flex; justify-content: center; margin-bottom: 20px; }
    #MainMenu, footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Function for logo
def get_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# --- HEADER ---
if LOGO_PATH.exists():
    logo_base64 = get_image_base64(LOGO_PATH)
    st.markdown(f'<img src="data:image/png;base64,{logo_base64}" class="logo-img">', unsafe_allow_html=True)
st.markdown('<div class="title-container"><h1 class="title">AURA</h1></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙️ CONFIG")
    v_type = st.radio("VOICE IDENTITY", ["Female", "Male"])
    st.divider()
    show_history = st.toggle("History Vault", value=False)
    if st.button("Wipe Session"):
        st.session_state.history = []
        st.rerun()

# --- BROWSER VOICE ENGINE ---
def trigger_voice(text, voice_pref):
    gender = "female" if voice_pref == "Female" else "male"
    if text:
        js_code = f"""
            <script>
                function runSpeech() {{
                    var voices = window.speechSynthesis.getVoices();
                    var msg = new SpeechSynthesisUtterance({json.dumps(text)});
                    var targetVoice = voices.find(v => {{
                        var n = v.name.toLowerCase();
                        var g = '{gender}';
                        if (g === 'female') {{
                            return n.includes('female') || n.includes('zira') || n.includes('samantha') || n.includes('google us english');
                        }} else {{
                            return n.includes('male') || n.includes('david') || n.includes('alex') || n.includes('google uk english male');
                        }}
                    }});
                    msg.voice = targetVoice || voices[0];
                    msg.rate = 1.1; 
                    window.speechSynthesis.cancel();
                    window.speechSynthesis.speak(msg);
                }}
                if (window.speechSynthesis.onvoiceschanged !== undefined) {{
                    window.speechSynthesis.onvoiceschanged = runSpeech;
                }}
                runSpeech(); 
            </script>
        """
        st.components.v1.html(js_code, height=0)

# Orb State
status_msg = "AWAITING VOICE INPUT"
orb_class = "active"
if st.session_state.speak_text:
    orb_class = "speaking"; status_msg = "AURA IS RESPONDING"

st.markdown(f'<div class="orb-box"><div class="orb {orb_class}"></div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="status">{status_msg}</div>', unsafe_allow_html=True)

# --- VOICE RECORDER ---
st.markdown('<div class="mic-container">', unsafe_allow_html=True)
audio = mic_recorder(
    start_prompt="🎙️ CLICK TO SPEAK",
    stop_prompt="🛑 STOP RECORDING",
    just_once=True,
    use_container_width=False,
    format="webm",
    key='aura_mic'
)
st.markdown('</div>', unsafe_allow_html=True)

# --- PROCESSING ---
if audio:
    audio_bytes = audio['bytes']
    if audio_bytes:
        with st.spinner("Aura is thinking..."):
            try:
                # Convert bytes to audio
                r = sr.Recognizer()
                audio_file = io.BytesIO(audio_bytes)
                with sr.AudioFile(audio_file) as source:
                    audio_data = r.record(source)
                
                txt = r.recognize_google(audio_data)
                st.session_state.history.append({"role": "user", "text": txt})
                
                # BRAIN (Groq)
                client = Groq(api_key=api_key_system)
                msgs = [{"role": "system", "content": "You are Aura. Be natural and very concise."}]
                for turn in st.session_state.history[-4:]:
                    msgs.append({"role": "user" if turn['role']=='user' else "assistant", "content": turn['text']})
                
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, max_tokens=150)
                answer = res.choices[0].message.content
                
                save_to_db(txt, answer)
                st.session_state.history.append({"role": "bot", "text": answer})
                st.session_state.speak_text = answer
                st.rerun()

            except Exception as e:
                st.error(f"Could not understand: {str(e)}")

# --- VOICE TRIGGER ---
if st.session_state.speak_text:
    trigger_voice(st.session_state.speak_text, v_type)
    st.session_state.speak_text = None

# --- HISTORY ---
if show_history:
    st.divider(); st.markdown("### 🏛️ HISTORY VAULT")
    vault = get_vault_data()
    for entry in vault:
        with st.expander(f"📍 {entry[0]} | {entry[1][:25]}..."):
            st.write(f"**You:** {entry[1]}"); st.write(f"**Aura:** {entry[2]}")

if st.session_state.history:
    st.divider(); st.markdown("### 🧬 RECENT")
    for msg in reversed(st.session_state.history[-4:]):
        color = "#6366f1" if msg['role'] == "user" else "#ec4899"
        role = "👤 YOU" if msg['role'] == "user" else "✨ AURA"
        st.markdown(f'<div class="chat-card"><b style="color:{color};">{role}</b><br>{msg["text"]}</div>', unsafe_allow_html=True)

