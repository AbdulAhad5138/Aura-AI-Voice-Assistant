# ⚡ AURA | Hyper-Intelligent Voice Assistant

Aura is a futuristic, highly intelligent voice assistant built with **Streamlit** and powered by **Groq's Llama-3.3**. It redefines web-based voice AI by offering **real-time internet access**, a luxury neon interface, and a robust **hands-free conversation loop** that works seamlessly on desktop and mobile browsers.

![AURA UI](https://img.shields.io/badge/AURA-Hyper--Intelligent-6366f1?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-Dark-FF4B4B?style=for-the-badge&logo=Streamlit)
![Groq](https://img.shields.io/badge/Powered%20By-Groq-orange?style=for-the-badge)

## ✨ New Ultra-Features

- **🌍 Real-Time Web Search**: Aura is now connected to the internet via DuckDuckGo. Ask for news, stocks, or weather, and it will intelligently browse the web to give you the latest answers.
- **🔄 True Hands-Free Loop**: Activated by a single "AUTO-START" click, Aura enters a continuous cycle: *Listen → Think → Speak → Listen*. No need to keep pressing buttons.
- **🎙️ Male & Female Voices**: Switch instantly between Male and Female voice personalities directly from the sidebar.
- **🛡️ Titan Bridge 2.0**: A completely refactored JavaScript bridge that solves "Microphone Blocked" issues on mobile and secure browsers by using user-triggered activation.
- **🧠 Robust Neural Brain**: Enhanced error handling ensures Aura never crashes, even if a tool fails—it simply falls back to its internal knowledge.
- **🎨 Neon Glassmorphism UI**: A stunning visual experience with a pulsing "Living Orb" that reacts to thinking and speaking states.

## 🛠️ Tech Stack

- **Frontend/Backend**: Streamlit
- **Intelligence**: Groq Llama-3.3-70B-Versatile
- **Web Capabilities**: DuckDuckGo Search (DDGS)
- **Voice Engine**: Web Speech API (Client-side Speech-to-Text & Text-to-Speech)
- **Memory**: SQLite3 (Local Conversation Vault)

## 🚦 Quick Start

### Prerequisites
- Python 3.9+
- A [Groq API Key](https://console.groq.com/keys)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/AbdulAhad5138/Aura-AI-Voice-Assistant.git
   cd Aura-AI-Voice-Assistant
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Secrets**:
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=gsk_your_actual_key_here
   ```

4. **Run the App**:
   ```bash
   streamlit run streamlit_app.py
   ```

## 📱 Mobile Usage Guide
1. Open the app link on Chrome or Safari on your phone.
2. Select your preferred **Voice Gender** from the sidebar `>`.
3. Tap the **"🟢 AUTO-START"** button.
4. Allow Microphone permissions when prompted.
5. Speak naturally! The app will automatically listen again after replying.

## ☁️ Deployment on Streamlit Cloud
1. Push this code to your GitHub repo.
2. Connect your repo to [share.streamlit.io](https://share.streamlit.io).
3. In the App Settings, go to "Secrets" and paste your API key:
   ```toml
   GROQ_API_KEY = "your_key_here"
   ```
4. Deploy!

---
*Architected and Refined by [Abdul Ahad](https://github.com/AbdulAhad5138)*
