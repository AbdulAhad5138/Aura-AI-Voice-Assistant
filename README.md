# 🤖 AURA | Ultra-Smooth AI Voice Assistant

Aura is a premium, high-performance voice assistant built with **Streamlit** and powered by **Groq's Llama-3**. It features a luxury glassmorphic interface, lag-free voice recognition, and intelligent browser-side speech synthesis.

![AURA UI](https://img.shields.io/badge/AURA-Ultra--Smooth-6366f1?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-Dark-FF4B4B?style=for-the-badge&logo=Streamlit)
![Groq](https://img.shields.io/badge/Powered%20By-Groq-orange?style=for-the-badge)

## ✨ Key Features

- **🚀 Ultra-Smooth Performance**: Optimized low-latency loop for near-instant responses.
- **🎙️ Web-Based Voice Recording**: Uses `streamlit-mic-recorder` for seamless browser-to-server audio transfer.
- **🔊 Multi-Identity Speech**: Switch between male and female voice identities with browser-optimized synthesis.
- **🏛️ History Vault**: Persistently saves conversations in a local SQLite database for future reference.
- **🎨 Premium UI/UX**: Custom CSS with glassmorphism, pulse animations, and a responsive luxury layout.
- **🧠 Intelligent Brain**: Powered by Llama-3-70B-Versatile via Groq for fast, natural conversations.

## 🛠️ Tech Stack

- **Frontend**: Streamlit (with Custom CSS/JS Injection)
- **Backend**: Python
- **AI Model**: Llama-3-70B (via Groq Cloud)
- **Voice Stack**: `SpeechRecognition` (Recognition) + Browser `speechSynthesis` (Output)
- **Database**: SQLite3

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

2. **Setup virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_key_here
   ```

5. **Run the App**:
   ```bash
   streamlit run streamlit_app.py
   ```

## 📂 Project Structure

- `streamlit_app.py`: The main luxury interface and application logic.
- `aura_data/`: Directory for persistent data (Vault, Logo).
- `responses.py`: (Optional) Helper for pre-defined responses.
- `voice_chatbot_advanced.py`: CLI version of the advanced chatbot logic.

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---
*Created with ❤️ by [Abdul Ahad](https://github.com/AbdulAhad5138)*
