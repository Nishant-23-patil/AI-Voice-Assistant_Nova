# Nova - AI Voice Assistant 🎙️🤖

Nova is a fully integrated, locally-hosted AI voice assistant powered by **Google Gemini** (`gemini-2.5-flash-lite`), featuring a sleek Flask + SocketIO backend and a Jarvis-style frontend. It utilizes the Web Speech API for seamless Speech-to-Text (STT) and Text-to-Speech (TTS), enabling quick and natural voice interactions.

## ✨ Features

- **🧠 Conversational AI**: Powered by Google Gemini for smart, natural, and context-aware responses.
- **🖥️ System Control**: Execute local commands directly using your voice:
  - 🔊 Volume Control (Up, Down, Mute)
  - 🔋 Battery & System Status (CPU/RAM monitoring)
  - 💤 Power Management (Sleep, Restart, Shutdown)
- **🌐 Web & App Launcher**: Instantly open popular websites (Google, YouTube, GitHub, Spotify, WhatsApp) or local applications (Notepad, Calculator, VS Code, CMD).
- **📝 Note Taking**: Dictate notes, read saved notes, or clear them on command.
- **🌤️ Weather Updates**: Get real-time weather information for any city.
- **🎵 YouTube Integration**: Search or play songs directly on YouTube.
- **⚡ Real-time WebSocket**: Fast and responsive frontend-backend communication via Flask-SocketIO.

## 🛠️ Technology Stack

- **Backend**: Python, Flask, Flask-SocketIO
- **AI Model**: Google Gemini API (`gemini-2.5-flash-lite`)
- **System Integration**: `psutil`, `pyautogui`, `os`, `subprocess`
- **Frontend STT/TTS**: Web Speech API

## 🚀 Getting Started

### Prerequisites
Make sure you have Python installed. You'll also need a Gemini API key.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/nova-voice-assistant.git
   cd nova-voice-assistant
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If you plan to use system control features like volume or battery status, ensure `pyautogui` and `psutil` are installed.*

3. **Set up the API Key:**
   Open `app.py` and replace the `GEMINI_API_KEY` variable with your actual Google Gemini API key.

4. **Run Nova:**
   ```bash
   python app.py
   ```

5. **Access the Interface:**
   Open your browser and navigate to `http://localhost:5000`. Grant microphone permissions, say "Hey Nova", and start commanding!

## 💡 Usage Examples
- *"What's the weather like in New York?"*
- *"Open Visual Studio Code."*
- *"Mute the volume."*
- *"Take a note: Buy groceries tomorrow."*
- *"Tell me a joke about programming."*
- *"Check system status."*

## 📜 License
This project is open-source and available under the [MIT License](LICENSE).
