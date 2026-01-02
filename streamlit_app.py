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
from duckduckgo_search import DDGS

# --- CONFIGURATION (BEST PERFORMANCE) ---
ST_PAGE_TITLE = "AURA | Hyper-Intelligent Voice"
ST_PAGE_ICON = "⚡"
GROQ_MODEL = "llama-3.3-70b-versatile" # Smartest fast model

# Load Environment
load_dotenv()

# --- INITIALIZATION ---
st.set_page_config(page_title=ST_PAGE_TITLE, page_icon=ST_PAGE_ICON, layout="wide")

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "aura_data"
DATA_DIR.mkdir(exist_ok=True, parents=True)
DB_PATH = DATA_DIR / "aura_memory.db"
LOGO_PATH = BASE_DIR / "assets" / "logo.png"

# --- DATABASE & MEMORY (Robust) ---
def init_db():
    """Initialize SQLite database with error handling for read-only environments."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS memory_vault
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      timestamp TEXT, 
                      user_query TEXT, 
                      bot_response TEXT,
                      meta_info TEXT)''')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        # st.warning(f"⚠️ Memory Vault Error (Running in Stateless Mode): {e}")
        return False

def save_interaction(query, response, meta=""):
    try:
        if not DB_PATH.parent.exists(): return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO memory_vault (timestamp, user_query, bot_response, meta_info) VALUES (?, ?, ?, ?)",
                  (ts, query, response, meta))
        conn.commit()
        conn.close()
    except: pass

init_db()

# --- SESSION STATE ---
if 'history' not in st.session_state: st.session_state.history = []
if 'voice_active' not in st.session_state: st.session_state.voice_active = False # Main toggle
if 'audio_queue' not in st.session_state: st.session_state.audio_queue = None
if 'processing_state' not in st.session_state: st.session_state.processing_state = "idle" 

# API Key Check
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("🚨 CRITICAL: GROQ_API_KEY not found in .env file.")
    st.stop()

# --- TOOLS (WEB SEARCH) ---
def search_web(query):
    """Deep web search using DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if results:
                summary = "\n".join([f"- {r['title']}: {r['body']} ({r['href']})" for r in results])
                return summary
            return "No relevant search results found."
    except Exception as e:
        return f"Search error: {e}"

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the internet for real-time information, news, stocks, or facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query keywords",
                    }
                },
                "required": ["query"],
            },
        },
    }
]

# --- LUXURY UI DESIGN ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700&family=Syncopate:wght@400;700&display=swap');
    
    /* GLOBAL THEME */
    .stApp { background-color: #050505; color: #e2e8f0; font-family: 'Outfit', sans-serif; }
    
    /* LOGO & TITLE */
    .hero-container { text-align: center; margin-bottom: 2rem; }
    .neon-text { 
        font-family: 'Syncopate', sans-serif; 
        font-size: 3rem; 
        font-weight: 700;
        background: linear-gradient(90deg, #4f46e5, #ec4899, #4f46e5); 
        background-size: 200% auto;
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        animation: shine 4s linear infinite;
        letter-spacing: -2px;
    }
    @keyframes shine { to { background-position: 200% center; } }

    /* ORB ANIMATIONS */
    .orb-stage { display: flex; justify-content: center; height: 180px; align-items: center; position: relative; }
    .core-orb {
        width: 100px; height: 100px; border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #6366f1, #000);
        box-shadow: 0 0 40px rgba(99, 102, 241, 0.4);
        position: relative; z-index: 2;
        transition: all 0.5s ease;
    }
    .ring {
        position: absolute; border-radius: 50%; border: 1px solid rgba(255,255,255,0.1);
        top: 50%; left: 50%; transform: translate(-50%, -50%);
        animation: spin 10s linear infinite;
    }
    .r1 { width: 140px; height: 140px; border-top-color: #ec4899; animation-duration: 4s; }
    .r2 { width: 180px; height: 180px; border-bottom-color: #8b5cf6; animation-direction: reverse; animation-duration: 7s; }
    
    @keyframes spin { 100% { transform: translate(-50%, -50%) rotate(360deg); } }

    /* STATES */
    .status-badge { 
        text-align: center; margin-top: 1rem; 
        font-family: 'Syncopate'; font-size: 0.8rem; letter-spacing: 2px;
        color: #94a3b8;
    }
    
    /* Thinking State */
    .thinking .core-orb { animation: breathe 1.5s infinite alternate; background: radial-gradient(circle at 30% 30%, #ec4899, #000); box-shadow: 0 0 60px rgba(236, 72, 153, 0.6); }
    @keyframes breathe { from { transform: scale(0.95); } to { transform: scale(1.1); } }
    
    /* Speaking State */
    .speaking .core-orb { animation: vibe 0.2s infinite; background: radial-gradient(circle at 30% 30%, #10b981, #000); box-shadow: 0 0 60px rgba(16, 185, 129, 0.6); }
    @keyframes vibe { 0% { transform: translate(1px, 1px); } 100% { transform: translate(-1px, -1px); } }

    /* CHAT CARDS */
    .chat-row { display: flex; gap: 1rem; margin-bottom: 1rem; }
    .chat-row.user { flex-direction: row-reverse; }
    .bubble { 
        padding: 1rem 1.5rem; border-radius: 20px; max-width: 80%;
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05);
        backdrop-filter: blur(10px);
    }
    .user .bubble { background: rgba(99, 102, 241, 0.1); border-color: rgba(99, 102, 241, 0.3); }
    
    /* HIDE STREAMLIT UGLINESS */
    div[data-testid="stToolbar"] { visibility: hidden; }
    div[data-testid="stDecoration"] { visibility: hidden; }
    div[data-testid="stStatusWidget"] { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* HIDDEN INPUT HACK FIX - Make it clickable but invisible so focus works */
    div[data-testid="stChatInput"] { 
        position: fixed; bottom: 10px; left: 50%; transform: translateX(-50%); 
        width: 80% !important; z-index: 1000; opacity: 0;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER AREA ---
col_logo, col_title = st.columns([1, 6])
with col_title:
    st.markdown('<div class="hero-container"><div class="neon-text">AURA AI</div></div>', unsafe_allow_html=True)

# --- VISUAL ORB ---
def render_orb():
    state = st.session_state.processing_state
    css_class = ""
    status_text = "SYSTEM READY"
    
    # Check if we are ACTUALLY active (from toggle)
    # But for visuals, we use processing_state
    
    if state == "thinking":
        css_class = "thinking"
        status_text = "PROCESSING..."
    elif state == "speaking":
        css_class = "speaking"
        status_text = "SPEAKING..."
    elif st.session_state.voice_active: # If active but idle
        css_class = "active"
        status_text = "LISTENING..."
            
    st.markdown(f"""
        <div class="orb-stage {css_class}">
            <div class="ring r1"></div>
            <div class="ring r2"></div>
            <div class="core-orb"></div>
        </div>
        <div class="status-badge">{status_text}</div>
    """, unsafe_allow_html=True)

# --- THE TITAN BRIDGE (CLIENT-SIDE CLICK TO TRIGGER) ---
def titan_bridge():
    # Retrieve payload (text to speak)
    payload = st.session_state.audio_queue if st.session_state.audio_queue else ""
    
    js_code = f"""
        <style>
            .bridge-control {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 20px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                margin: 20px 0;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .mic-btn {{
                background: linear-gradient(135deg, #6366f1, #8b5cf6);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 30px;
                font-size: 1.2rem;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
                transition: transform 0.2s, box-shadow 0.2s;
                font-family: 'Outfit', sans-serif;
                text-transform: uppercase;
                letter-spacing: 1px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .mic-btn:hover {{ transform: scale(1.05); box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6); }}
            .mic-btn:active {{ transform: scale(0.95); }}
            .mic-btn.active {{ background: #ef4444; box-shadow: 0 0 20px rgba(239, 68, 68, 0.5); }}
            
            .indicator {{ margin-top: 10px; font-size: 0.9rem; color: #94a3b8; font-family: monospace; }}
        </style>

        <div class="bridge-control">
            <button id="micToggle" class="mic-btn" onclick="toggleVoice()">
                🎤 Activate System
            </button>
            <div id="statusInd" class="indicator">Click to Start Interaction</div>
        </div>

        <script>
            var speakText = {json.dumps(payload)};
            var recognition = null;
            var isListening = false;
            var synth = window.speechSynthesis;

            // --- UI UPDATE ---
            function updateUI(status, isActive) {{
                const btn = document.getElementById('micToggle');
                const ind = document.getElementById('statusInd');
                if(!btn || !ind) return;
                
                ind.innerText = status;
                if (isActive) {{
                    btn.classList.add('active');
                    btn.innerHTML = "🛑 Stop / Reset";
                }} else {{
                    btn.classList.remove('active');
                    btn.innerHTML = "🎤 Activate System";
                }}
            }}

            // --- PYTHON BRIDGE ---
            function bridgeToPython(text) {{
                const input = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
                const submit = window.parent.document.querySelector('button[data-testid="stChatInputSubmitButton"]');
                if (input) {{
                    // Set value
                    const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                    nativeTextAreaValueSetter.call(input, text);
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    
                    // Click submit
                    setTimeout(() => {{
                        if (submit) submit.click();
                        else {{
                            const enter = new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }});
                            input.dispatchEvent(enter);
                        }}
                    }}, 100);
                }}
            }}

            // --- SPEECH RECOGNITION ---
            function initRecognition() {{
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {{
                    alert("⚠️ Browser not supported. Use Chrome/Edge.");
                    return null;
                }}
                
                const r = new SpeechRecognition();
                r.lang = 'en-US';
                r.continuous = false;
                r.interimResults = false;
                
                r.onstart = () => updateUI("👂 Listening...", true);
                r.onend = () => {{
                    // Auto-restart if we think we should be listening? 
                    // No, let's keep it manual/controlled for stability. 
                    if (isListening) {{
                         // If it stopped unexpectedly, restart
                         try {{ r.start(); }} catch(e) {{}}
                    }} else {{
                         updateUI("💤 Interaction Paused", false);
                    }}
                }};
                
                r.onresult = (e) => {{
                    const t = e.results[0][0].transcript;
                    isListening = false; // Stop listening while processing
                    r.stop();
                    updateUI("✨ Heard: " + t, true);
                    bridgeToPython(t);
                }};
                
                r.onerror = (e) => {{
                    console.warn(e.error);
                    if (e.error === 'not-allowed') {{
                        isListening = false;
                        updateUI("⚠️ Access Denied", false);
                        alert("⚠️ MICROPHONE BLOCKED. Check URL bar permission.");
                    }}
                }};
                
                return r;
            }}

            // --- TTS ---
            function speak(text) {{
                if (!text) return;
                synth.cancel();
                
                // Stop listening so we don't hear ourselves
                if (recognition) {{
                    recognition.stop(); 
                    isListening = false;
                }}
                
                const utter = new SpeechSynthesisUtterance(text);
                const voices = synth.getVoices();
                const target = voices.find(v => v.name.includes("Google US English") || v.name.includes("Samantha")) || voices[0];
                
                utter.voice = target;
                utter.rate = 1.1;
                
                utter.onstart = () => updateUI("🔉 Speaking...", true);
                
                utter.onend = () => {{
                    // Resume listening if we were in a "chat mode"
                    // For manual button approach, we might want to wait for user?
                    // Let's AUTO-RESUME listening to keep the conversation flowing!
                    updateUI("👂 Listening...", true);
                    isListening = true;
                    if(!recognition) recognition = initRecognition();
                    try {{ recognition.start(); }} catch(e) {{}}
                }};
                
                synth.speak(utter);
            }}

            // --- MAIN TOGGLE ---
            function toggleVoice() {{
                if (!recognition) recognition = initRecognition();
                
                // If currently speaking, stop everything
                if (synth.speaking) {{
                    synth.cancel();
                    isListening = false;
                    if(recognition) recognition.stop();
                    updateUI("💤 Force Stopped", false);
                    return;
                }}

                if (!isListening) {{
                    // START LISTENING
                    isListening = true;
                    try {{ recognition.start(); }} catch(e) {{}}
                    
                    // If we have pending text to speak (from Python load), speak it now!
                    if (speakText && speakText.length > 0) {{
                        speak(speakText);
                    }}
                }} else {{
                    // STOP
                    isListening = false;
                    recognition.stop();
                    synth.cancel();
                    updateUI("💤 System Offline", false);
                }}
            }}
            
            // --- ON LOAD ---
            // If we have text to speak, we can't auto-speak without click.
            // We gently prompt the user or rely on the toggle.
            if (speakText && speakText.length > 0) {{
                 setTimeout(() => {{
                     const ind = document.getElementById('statusInd');
                     if(ind) ind.innerText = "💬 Response Ready! Click 'Activate' to hear it.";
                 }}, 200);
            }}

        </script>
    """
    st.components.v1.html(js_code, height=180)

# --- BRAIN (GROQ + TOOLS) ---
def process_brain(user_input):
    client = Groq(api_key=api_key)
    
    # 1. Build Context
    sys_prompt = """
    You are AURA, an advanced AI.
    Traits: Intelligent, Fast, Helpful. 
    
    TOOL USE RULES:
    - If the user asks for current info/news, YOU MUST USE THE search_web TOOL.
    - AFTER calling the tool, you will receive the search results. 
    - You MUST then read those results and Synthesize a clear, direct answer to the user's question.
    - Do NOT just say "search results found". Answer the question using the data!
    - Keep voice answers concise (under 2 sentences) but informative.
    """
    
    messages = [{"role": "system", "content": sys_prompt}]
    
    # Add recent history
    recent_history = st.session_state.history[-4:]
    for turn in recent_history:
        messages.append({"role": turn["role"], "content": turn["content"]})
    
    messages.append({"role": "user", "content": user_input})
    
    # 2. Inference
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=256
        )
        
        msg = completion.choices[0].message
        
        # 3. Tool Calling Handling
        if msg.tool_calls:
            st.session_state.processing_state = "thinking"
            render_orb() 
            
            tool_call = msg.tool_calls[0]
            if tool_call.function.name == "search_web":
                args = json.loads(tool_call.function.arguments)
                st.toast(f"🔎 Searching Web: {args['query']}")
                search_res = search_web(args['query'])
                
                # Feed tool output back
                messages.append(msg)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(search_res)
                })
                
                # Final response (Second Turn)
                # We need to tell the model to use the tool info to answer
                final_res = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=messages,
                    max_tokens=256
                )
                return final_res.choices[0].message.content
                
        return msg.content

    except Exception as e:
        # Fallback
        if "tool_use_failed" in str(e) or "400" in str(e):
             st.error("Tool Error - Retrying basic response")
             try:
                 messages.append({"role": "user", "content": "Please answer without tools if possible."})
                 completion = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=messages,
                    max_tokens=256
                )
                 return completion.choices[0].message.content
             except:
                 pass
        return f"I encountered a neural error: {str(e)}"

# --- MAIN CONTROLLER ---

# 1. SETTINGS (Moved to Main Page for Mobile Access)
with st.expander("⚙️ Settings & Customization", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        # Voice Gender Selection
        if 'v_gender' not in st.session_state: st.session_state.v_gender = "Female"
        st.session_state.v_gender = st.radio("Voice Identity", ["Female", "Male"], horizontal=True)
    with c2:
        st.write("") # Spacer
        if st.button("🗑️ Clear Memory Cache"):
            st.session_state.history = []
            st.rerun()

# 2. Render Orb
render_orb()

# --- THE TITAN BRIDGE (HANDS-FREE LOOP) ---
def titan_bridge():
    # Retrieve payload
    payload = st.session_state.audio_queue if st.session_state.audio_queue else ""
    is_active = st.session_state.voice_active
    gender_pref = st.session_state.v_gender.lower()
    
    js_code = f"""
        <style>
            .bridge-control {{ display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; background: rgba(255, 255, 255, 0.05); border-radius: 12px; margin: 20px 0; border: 1px solid rgba(255, 255, 255, 0.1); }}
            .mic-btn {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; border: none; padding: 15px 30px; border-radius: 30px; font-size: 1.2rem; font-weight: bold; cursor: pointer; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4); transition: transform 0.2s; font-family: 'Outfit', sans-serif; display: flex; align-items: center; gap: 10px; }}
            .mic-btn:hover {{ transform: scale(1.05); }}
            .mic-btn.active {{ background: #ef4444; box-shadow: 0 0 20px rgba(239, 68, 68, 0.5); }}
            .indicator {{ margin-top: 10px; font-size: 0.9rem; color: #94a3b8; font-family: monospace; }}
        </style>

        <div class="bridge-control">
            <button id="micToggle" class="mic-btn" onclick="toggleVoice()">
                🎤 Activate System
            </button>
            <div id="statusInd" class="indicator">Click to Start Interaction</div>
        </div>

        <script>
            var speakText = {json.dumps(payload)};
            var isActive = {json.dumps(is_active)};
            var genderPref = "{gender_pref}";
            
            var recognition = null;
            var isListening = false;
            var synth = window.speechSynthesis;

            function updateUI(status, active) {{
                const btn = document.getElementById('micToggle');
                const ind = document.getElementById('statusInd');
                if(!btn || !ind) return;
                ind.innerText = status;
                if (active) {{
                    btn.classList.add('active');
                    btn.innerHTML = "🛑 Stop / Reset";
                }} else {{
                    btn.classList.remove('active');
                    btn.innerHTML = "🎤 Activate System";
                }}
            }}

            function bridgeToPython(text) {{
                const input = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
                const submit = window.parent.document.querySelector('button[data-testid="stChatInputSubmitButton"]');
                if (input) {{
                    const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                    nativeTextAreaValueSetter.call(input, text);
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    setTimeout(() => {{
                        if (submit) submit.click();
                        else {{
                            const enter = new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }});
                            input.dispatchEvent(enter);
                        }}
                    }}, 100);
                }}
            }}

            function initRecognition() {{
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) return null;
                const r = new SpeechRecognition();
                r.lang = 'en-US';
                r.continuous = false;
                r.interimResults = false;
                r.onstart = () => updateUI("👂 Listening...", true);
                r.onend = () => {{
                    if (isListening) {{
                         try {{ r.start(); }} catch(e) {{}}
                    }}
                }};
                r.onresult = (e) => {{
                    const t = e.results[0][0].transcript;
                    isListening = false; // Stop listening to process
                    r.stop();
                    updateUI("✨ Heard: " + t, true);
                    bridgeToPython(t);
                }};
                return r;
            }}

            function speak(text) {{
                if (!text) return;
                synth.cancel();
                if (recognition) {{ recognition.stop(); isListening = false; }}
                
                const utter = new SpeechSynthesisUtterance(text);
                const voices = synth.getVoices();
                
                // Gender Selection Logic
                let target = null;
                if (genderPref === 'male') {{
                    target = voices.find(v => v.name.toLowerCase().includes("male") || v.name.includes("David") || v.name.includes("Microsoft")) || voices[0];
                }} else {{
                    target = voices.find(v => v.name.toLowerCase().includes("female") || v.name.includes("Google US English") || v.name.includes("Samantha")) || voices[0];
                }}
                
                utter.voice = target;
                utter.rate = 1.1;
                
                utter.onstart = () => updateUI("🔉 Speaking...", true);
                utter.onend = () => {{
                    // AUTO-RESUME LISTENING (HANDS FREE)
                    updateUI("👂 Listening...", true);
                    isListening = true;
                    if(!recognition) recognition = initRecognition();
                    try {{ recognition.start(); }} catch(e) {{}}
                }};
                
                synth.speak(utter);
            }}

            function toggleVoice() {{
                // This function is manually clicking the button
                // It toggles the global state visually, but actually we rely on 'isActive' from Python for logic
                if (!recognition) recognition = initRecognition();
                
                if (synth.speaking || isListening) {{
                     // Stop
                     synth.cancel();
                     isListening = false;
                     recognition.stop();
                     updateUI("💤 Paused", false);
                }} else {{
                     // Start
                     isListening = true;
                     try {{ recognition.start(); }} catch(e) {{}}
                }}
            }}
            
            // --- AUTO-RUN LOGIC (The Fix) ---
            if (isActive) {{
                // If Python says we are active (meaning user clicked it previously)
                // We try to resume immediately.
                if (speakText) {{
                    setTimeout(() => speak(speakText), 500); 
                }} else {{
                    setTimeout(() => {{
                        if (!recognition) recognition = initRecognition();
                        isListening = true;
                        try {{ recognition.start(); }} catch(e) {{}}
                    }}, 500);
                }}
            }}

        </script>
    """
    st.components.v1.html(js_code, height=180)

# 3. Render Manual Bridge (The Microphone Button)
if 'voice_active' not in st.session_state: st.session_state.voice_active = False

# We need a way to Toggle Active State in Python so it persists
# The previous button handled this inside the Js effectively, but we need Python to know.
# Actually, the 'Hands Free' relies on Python re-rendering with is_active=True.
# We'll use a hidden button or just rely on the fact that if 'audio_queue' is present, we imply active?
# No, we need an explicit toggle.

# Let's add a REAL Python toggle to control "System Power"
# We'll put it above the bridge or use the sidebar
col_c1, col_c2 = st.columns([1,1])
with col_c1:
    # If user clicks this, we set voice_active = True
    # The JS will then see isActive=True and auto-start.
    if st.button("🔴 RESET / STOP"):
        st.session_state.voice_active = False
        st.rerun()

with col_c2:
    if not st.session_state.voice_active:
        if st.button("🟢 AUTO-START"):
            st.session_state.voice_active = True
            st.rerun()
    else:
        st.success("System Active")

titan_bridge()

# 4. Hidden Input & Logic Loop
user_input = st.chat_input("Type or Speak...", key="main_input") # Receiver for JS

if user_input:
    # Set state
    st.session_state.processing_state = "thinking"
    st.session_state.history.append({"role": "user", "content": user_input})
    
    # Process
    with st.spinner("Processing..."):
        response = process_brain(user_input)
    
    # Save
    st.session_state.history.append({"role": "assistant", "content": response})
    st.session_state.audio_queue = response # Set for TTS
    st.session_state.processing_state = "speaking"
    
    save_interaction(user_input, response)
    st.rerun()

# 5. Clear queue after render if it was consumed? 
# Actually we need it to persist for the JS to read it on this run.
# The JS reads `speakText` from python on load.
# We clear it on the *next* run or never? 
# Streamlit re-runs script top-to-bottom. 
# If we clear it here, next re-run will be empty. That is correct.
# BUT wait, the `titan_bridge` function runs above. It has ALREADY read the queue into the JS string.
# So we can safely clear it here so it doesn't speak again on next refresh.
st.session_state.audio_queue = None

# 6. Display History
if st.session_state.history:
    st.markdown("<br>", unsafe_allow_html=True)
    for msg in reversed(st.session_state.history[-6:]):
        role_cls = "user" if msg["role"] == "user" else "aura"
        st.markdown(f"""
            <div class="chat-row {role_cls}">
                <div class="bubble">
                    <small style="opacity:0.5">{msg['role'].upper()}</small><br>
                    {msg['content']}
                </div>
            </div>
        """, unsafe_allow_html=True)
