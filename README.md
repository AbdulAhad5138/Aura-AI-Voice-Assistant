# 🤖 AURA | Supreme Alexa Voice Assistant

Aura is a premium, high-performance voice assistant built with **Streamlit** and powered by **Groq's Llama-3**. It features a luxury glassmorphic interface and a revolutionary **Supreme Global Node** architecture that allows for a 100% hands-free, Alexa-style conversation loop both locally and on Streamlit Cloud.

![AURA UI](https://img.shields.io/badge/AURA-Supreme-6366f1?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-Dark-FF4B4B?style=for-the-badge&logo=Streamlit)
![Groq](https://img.shields.io/badge/Powered%20By-Groq-orange?style=for-the-badge)

## ✨ Key Features

- **🔄 Infinite Alexa Loop**: Once activated, Aura listens, thinks, and speaks in a continuous cycle. No button-pressing required.
- **🌐 Universal Cloud Bridge**: Uses client-side browser intelligence to handle voice recording and synthesis. This eliminates the "No Microphone" errors common on cloud platforms.
- **🔊 Multi-Identity Speech**: High-fidelity Male and Female voice identities with natural inflections.
- **🏛️ Neural Vault**: Advanced SQLite-based long-term memory that captures and preserves every conversation turn.
- **🎨 Luxury Aesthetics**: State-of-the-art UI with glassmorphism, pulse animations, and "Active Synapse" cards.
- **🚀 Newest-First Synapses**: Live conversation logs that automatically show the most recent turn at the top for easy reading.

## 🛠️ Tech Stack

- **Frontend/Backend**: Streamlit
- **Brain**: Groq Llama-3-70B (State-of-the-art LLM)
- **Voice Logic**: Web Speech API (Client-side Recognition & Synthesis)
- **Database**: SQLite3
- **Security**: Hidden API Key management via `.env` or Streamlit Secrets.

## 🚦 Getting Started

### Prerequisites

- Python 3.8+
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

3. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_key_here
   ```

4. **Run the App**:
   ```bash
   streamlit run streamlit_app.py
   ```

### ☁️ Streamlit Cloud Deployment
For live deployment, add your `GROQ_API_KEY` to the **Secrets** section in the Streamlit Dashboard.

## 📂 Project Structure

- `streamlit_app.py`: The supreme luxury interface and automated loop logic.
- `assets/`: Directory for premium assets like the holographic logo.
- `aura_data/`: Directory for persistent SQLite conversation vault.

---
*Created with ❤️ by [Abdul Ahad](https://github.com/AbdulAhad5138)*
