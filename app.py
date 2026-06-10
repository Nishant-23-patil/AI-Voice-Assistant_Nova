import os
import re
import sys
import math
import json
import random
import datetime
import subprocess
import webbrowser
import urllib.parse

from flask import Flask, render_template, request, jsonify

# ── Optional: Wikipedia ───────────────────────────────
try:
    import wikipedia
    WIKI = True
except ImportError:
    WIKI = False

# ── Optional: Windows volume control ─────────────────
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    VOLUME_CTRL = True
except Exception:
    VOLUME_CTRL = False

ASSISTANT = "Nova"
USER      = "Nishant"

app = Flask(__name__)
app.config["SECRET_KEY"] = "nova-local-nlp-2026"

# ════════════════════════════════════════════════════
#  JOKES BANK
# ════════════════════════════════════════════════════
JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "How many programmers does it take to change a light bulb? None — that's a hardware problem.",
    "Why did the developer go broke? Because he used up all his cache.",
    "I asked Siri to call me an ambulance. Now my phone calls me 'an ambulance'.",
    "Why do Java developers wear glasses? Because they don't C#.",
    "What's a computer's favourite snack? Microchips!",
    "I named my dog 'Stay'. Now I can't call him. 'Come here, Stay. Come here, Stay.'",
    "Why can't you trust an atom? Because they make up literally everything.",
    "What do you call a bear with no teeth? A gummy bear!",
    "Why did the math book look so sad? Because it had too many problems.",
]

# ════════════════════════════════════════════════════
#  KNOWN APPS  (name → executable path or command)
# ════════════════════════════════════════════════════
APPS = {
    "notepad":        "notepad.exe",
    "calculator":     "calc.exe",
    "paint":          "mspaint.exe",
    "word":           "WINWORD.EXE",
    "excel":          "EXCEL.EXE",
    "powerpoint":     "POWERPNT.EXE",
    "chrome":         r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome":  r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "brave":          r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    "vlc":            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "spotify":        r"C:\Users\HP\AppData\Roaming\Spotify\Spotify.exe",
    "vscode":         r"C:\Users\HP\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "vs code":        r"C:\Users\HP\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "visual studio code": r"C:\Users\HP\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "file explorer":  "explorer.exe",
    "explorer":       "explorer.exe",
    "task manager":   "taskmgr.exe",
    "cmd":            "cmd.exe",
    "command prompt": "cmd.exe",
    "whatsapp":       r"C:\Users\HP\AppData\Local\WhatsApp\WhatsApp.exe",
    "telegram":       r"C:\Users\HP\AppData\Roaming\Telegram Desktop\Telegram.exe",
    "discord":        r"C:\Users\HP\AppData\Local\Discord\app-\Discord.exe",
    "zoom":           r"C:\Users\HP\AppData\Roaming\Zoom\bin\Zoom.exe",
    "skype":          r"C:\Program Files\Microsoft\Skype for Desktop\Skype.exe",
    "settings":       "ms-settings:",
    "control panel":  "control",
    "snipping tool":  "snippingtool.exe",
    "clock":          "ms-clock:",
    "camera":         "microsoft.windows.camera:",
}

WEBSITES = {
    "youtube":    "https://youtube.com",
    "google":     "https://google.com",
    "gmail":      "https://mail.google.com",
    "github":     "https://github.com",
    "facebook":   "https://facebook.com",
    "instagram":  "https://instagram.com",
    "twitter":    "https://twitter.com",
    "whatsapp":   "https://web.whatsapp.com",
    "linkedin":   "https://linkedin.com",
    "stackoverflow": "https://stackoverflow.com",
    "reddit":     "https://reddit.com",
    "wikipedia":  "https://wikipedia.org",
    "netflix":    "https://netflix.com",
    "amazon":     "https://amazon.in",
    "flipkart":   "https://flipkart.com",
    "hotstar":    "https://hotstar.com",
}

# ════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════
def _open_app(name: str) -> str:
    key = name.lower().strip()
    path = APPS.get(key)
    if path:
        try:
            if path.startswith("ms-"):
                os.startfile(path)
            else:
                subprocess.Popen(path, shell=True)
            return f"Opening {name} for you!"
        except Exception as e:
            return f"I couldn't open {name}. Error: {e}"
    return None

def _open_website(url: str, label: str = "") -> str:
    webbrowser.open(url)
    return f"Opening {label or url} in your browser!"

def _get_volume() -> int:
    if not VOLUME_CTRL:
        return -1
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    return int(volume.GetMasterVolumeLevelScalar() * 100)

def _set_volume(level: int) -> str:
    if not VOLUME_CTRL:
        # Fallback: use nircmd or powershell
        try:
            level_clamped = max(0, min(100, level))
            # PowerShell fallback
            ps_cmd = f"(New-Object -ComObject WScript.Shell).SendKeys([char]174)"
            # Use direct Windows API via SndVol
            subprocess.run(
                ["powershell", "-c",
                 f"$obj = New-Object -ComObject WScript.Shell; "
                 f"Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class Vol {{ [DllImport(\"user32.dll\")] public static extern int SendMessage(int hWnd, int Msg, int wParam, int lParam); }}'; "
                 f""],
                capture_output=True
            )
            return f"Volume control module not available. Please install pycaw."
        except:
            return "Volume control is not available on this system."
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        level_clamped = max(0.0, min(1.0, level / 100.0))
        volume.SetMasterVolumeLevelScalar(level_clamped, None)
        return f"Volume set to {level} percent!"
    except Exception as e:
        return f"Could not set volume: {e}"

def _calc_expr(expr: str) -> str:
    try:
        # Allow only safe math operations
        safe = re.sub(r'[^0-9\+\-\*\/\.\(\)\s\%\^]', '', expr)
        safe = safe.replace('^', '**')
        result = eval(safe, {"__builtins__": {}, "math": math})
        return f"The answer is {result}"
    except:
        return None

def _wikipedia_search(query: str) -> str:
    if not WIKI:
        url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"I opened Wikipedia for {query} in your browser."
    try:
        wikipedia.set_lang("en")
        summary = wikipedia.summary(query, sentences=2, auto_suggest=True)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        try:
            summary = wikipedia.summary(e.options[0], sentences=2)
            return summary
        except:
            return f"I found multiple results for {query}. Could you be more specific?"
    except Exception:
        url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"I opened Wikipedia for {query} in your browser."

# ════════════════════════════════════════════════════
#  SMALL TALK RESPONSES
# ════════════════════════════════════════════════════
SMALL_TALK = {
    r"(how are you|how do you do|how are you doing|you okay)": [
        "I'm running at full power and ready to assist you!",
        "All systems nominal! I'm doing great, thanks for asking.",
        "Perfectly calibrated and ready to go!",
    ],
    r"(what is your name|who are you|what are you called|your name)": [
        f"I am {ASSISTANT}, your personal AI voice assistant.",
        f"My name is {ASSISTANT}. I'm here to help you with anything!",
    ],
    r"(who made you|who created you|who built you|who is your creator)": [
        f"I was built by {USER} using Python, Flask, and the Web Speech API.",
        f"I was created by {USER}. He's brilliant, right?",
    ],
    r"(thank you|thanks|thank u|thx|thank you so much)": [
        "You're welcome! Anything else I can help with?",
        "Happy to help! Let me know if you need anything else.",
        "Anytime! That's what I'm here for.",
    ],
    r"(hello|hi|hey|good morning|good evening|good afternoon|good night)": [
        f"Hello {USER}! How can I assist you today?",
        f"Hey there! Nova online and ready.",
        f"Hi {USER}! What can I do for you?",
    ],
    r"(bye|goodbye|see you|shut down|exit|quit)": [
        "Goodbye! See you soon.",
        "Signing off. Call me anytime!",
        "Bye! Stay awesome.",
    ],
    r"(what can you do|help me|your features|capabilities|what do you know)": [
        "I can open apps, search the web, tell jokes, check the time and date, do math, search Wikipedia, control your system volume, and have a conversation with you — all without any internet API!",
    ],
    r"(i love you|i like you)": [
        "That's very kind of you! I'm always here for you.",
        "Aww, thank you! I'm just a voice, but I appreciate it.",
    ],
    r"(are you human|are you a robot|are you ai|are you real)": [
        "I'm an AI voice assistant named Nova. Not human, but I'll do my best!",
        "I'm artificial intelligence — but my helpfulness is very real!",
    ],
}

# ════════════════════════════════════════════════════
#  INTENT PATTERNS
# ════════════════════════════════════════════════════
INTENTS = [
    # Time
    (r"\b(time|what time|current time|tell me the time)\b", "get_time"),
    # Date
    (r"\b(date|today|what day|what is today|current date)\b", "get_date"),
    # Joke
    (r"\b(joke|funny|make me laugh|tell me a joke|say something funny)\b", "joke"),
    # Open app
    (r"\b(open|launch|start|run)\b (.+)", "open_app"),
    # Close app
    (r"\b(close|shut|kill|stop)\b (.+)", "close_app"),
    # Volume set
    (r"\b(set volume|volume to|set the volume)\b.*?(\d+)", "set_volume"),
    # Volume up
    (r"\b(volume up|increase volume|louder|turn up)\b", "volume_up"),
    # Volume down
    (r"\b(volume down|decrease volume|quieter|lower volume|turn down)\b", "volume_down"),
    # Mute
    (r"\b(mute|silence|quiet)\b", "mute"),
    # Wikipedia
    (r"\b(wikipedia|wiki|tell me about|who is|what is|what are|explain|define|definition of)\b (.+)", "wikipedia"),
    # Math / calculate
    (r"\b(calculate|compute|math|what is|solve)\b (.+[\d\+\-\*\/\^\%]+.*)","calc"),
    (r"(\d+[\s\+\-\*\/\^\%]+[\d\s\+\-\*\/\^\%\(\)\.]+)", "calc_direct"),
    # YouTube search
    (r"\b(play|search on youtube|youtube)\b (.+)", "youtube_search"),
    # Google search
    (r"\b(search|google|find|look up|search for)\b (.+)", "google_search"),
    # Open website
    (r"\b(open|go to|visit|browse)\b (.+\.com|.+\.in|.+\.org|.+\.net|.+\.io)", "open_website"),
    # Weather
    (r"\b(weather|temperature|forecast|how hot|how cold)\b", "weather"),
    # News
    (r"\b(news|headlines|latest news|top news)\b", "news"),
    # Screenshot
    (r"\b(screenshot|screen capture|take a screenshot)\b", "screenshot"),
    # Shutdown
    (r"\b(shutdown|shut down|turn off|power off)\b", "shutdown"),
    # Restart
    (r"\b(restart|reboot)\b", "restart"),
    # Sleep
    (r"\b(sleep|hibernate|suspend)\b", "sleep"),
    # Lock
    (r"\b(lock|lock screen|lock the screen)\b", "lock"),
    # Battery
    (r"\b(battery|battery level|charge|charging)\b", "battery"),
    # IP address
    (r"\b(ip address|my ip|what is my ip)\b", "ip_address"),
    # Flip coin
    (r"\b(flip a coin|heads or tails|coin flip)\b", "flip_coin"),
    # Roll dice
    (r"\b(roll a dice|roll dice|dice|roll)\b", "roll_dice"),
    # Alarm / reminder
    (r"\b(remind me|set a reminder|alarm)\b", "reminder"),
]

# ════════════════════════════════════════════════════
#  INTENT HANDLERS
# ════════════════════════════════════════════════════
def handle_get_time():
    now = datetime.datetime.now()
    hour = now.strftime("%I").lstrip("0") or "12"
    minute = now.strftime("%M")
    ampm = now.strftime("%p")
    return f"The current time is {hour}:{minute} {ampm}."

def handle_get_date():
    now = datetime.datetime.now()
    return f"Today is {now.strftime('%A, %d %B %Y')}."

def handle_joke():
    return random.choice(JOKES)

def handle_open_app(match, c):
    # Try to extract app name from matched group
    target = match.group(2).strip() if match.lastindex and match.lastindex >= 2 else ""
    # Remove trailing filler words
    target = re.sub(r'\b(app|application|program|software|please|now|for me)\b', '', target).strip()

    # First try direct app match
    result = _open_app(target)
    if result:
        return result

    # Try website if it looks like a site name
    site_key = target.lower().replace(" ", "")
    for key, url in WEBSITES.items():
        if key in site_key or site_key in key:
            return _open_website(url, key.capitalize())

    # If still nothing, try as app name partially
    for key in APPS:
        if target.lower() in key or key in target.lower():
            return _open_app(key)

    return f"I don't know how to open '{target}'. You can add it to my app list!"

def handle_close_app(match, c):
    target = match.group(2).strip() if match.lastindex and match.lastindex >= 2 else ""
    target = re.sub(r'\b(app|application|program|software)\b', '', target).strip()
    try:
        subprocess.run(f"taskkill /f /im {target}.exe", shell=True, capture_output=True)
        return f"Closing {target}."
    except:
        return f"I couldn't close {target}."

def handle_set_volume(match):
    level = int(match.group(2))
    return _set_volume(level)

def handle_volume_up():
    if VOLUME_CTRL:
        cur = _get_volume()
        new = min(100, cur + 10)
        return _set_volume(new)
    try:
        from ctypes import windll
        windll.winmm.waveOutSetVolume(0, 0xFFFF * 80 // 100 | (0xFFFF * 80 // 100) << 16)
    except:
        pass
    return "Turning volume up!"

def handle_volume_down():
    if VOLUME_CTRL:
        cur = _get_volume()
        new = max(0, cur - 10)
        return _set_volume(new)
    return "Turning volume down!"

def handle_mute():
    if VOLUME_CTRL:
        return _set_volume(0)
    return "Muting audio!"

def handle_wikipedia(match, c):
    # Strip intent keywords
    query = match.group(2).strip() if match.lastindex and match.lastindex >= 2 else c
    query = re.sub(r'\b(wikipedia|wiki|tell me about|who is|what is|what are|explain|define|definition of)\b', '', query, flags=re.I).strip()
    if not query:
        return "What topic would you like me to look up on Wikipedia?"
    return _wikipedia_search(query)

def handle_calc(match, c):
    expr = match.group(2) if match.lastindex and match.lastindex >= 2 else match.group(1)
    # Remove filler words
    expr = re.sub(r'\b(calculate|compute|math|what is|solve|the answer to|equals?)\b', '', expr, flags=re.I).strip()
    result = _calc_expr(expr)
    return result or f"I couldn't compute that. Try a cleaner expression."

def handle_youtube(match):
    query = match.group(2).strip() if match.lastindex and match.lastindex >= 2 else ""
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    webbrowser.open(url)
    return f"Searching YouTube for {query}!"

def handle_google_search(match):
    query = match.group(2).strip() if match.lastindex and match.lastindex >= 2 else ""
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    webbrowser.open(url)
    return f"Searching Google for {query}!"

def handle_open_website(match, c):
    target = match.group(2).strip() if match.lastindex and match.lastindex >= 2 else ""
    target = re.sub(r'\b(open|go to|visit|browse)\b', '', target, flags=re.I).strip()
    # Check known sites
    for key, url in WEBSITES.items():
        if key in target.lower():
            return _open_website(url, key.capitalize())
    # Treat raw as URL
    if not target.startswith("http"):
        target = "https://" + target
    webbrowser.open(target)
    return f"Opening {target} in your browser!"

def handle_weather():
    webbrowser.open("https://www.google.com/search?q=weather+today")
    return "Opening weather information in your browser!"

def handle_news():
    webbrowser.open("https://news.google.com")
    return "Opening Google News for you!"

def handle_screenshot():
    try:
        subprocess.Popen("snippingtool.exe", shell=True)
        return "Opening Snipping Tool for a screenshot!"
    except:
        return "I couldn't open the snipping tool."

def handle_shutdown():
    return "Shutdown command requires confirmation. Please type 'confirm shutdown' for safety."

def handle_confirmed_shutdown():
    os.system("shutdown /s /t 5")
    return "Shutting down your PC in 5 seconds. Goodbye!"

def handle_restart():
    os.system("shutdown /r /t 5")
    return "Restarting your PC in 5 seconds!"

def handle_sleep():
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    return "Putting your PC to sleep. Good night!"

def handle_lock():
    os.system("rundll32.exe user32.dll,LockWorkStation")
    return "Locking your screen. Stay safe!"

def handle_battery():
    try:
        import psutil
        bat = psutil.sensors_battery()
        if bat:
            status = "charging" if bat.power_plugged else "on battery"
            return f"Battery is at {int(bat.percent)} percent and {status}."
        return "I couldn't read the battery level."
    except ImportError:
        return "Battery module not available. Install psutil."

def handle_ip():
    try:
        import socket
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return f"Your local IP address is {ip}."
    except:
        return "I couldn't retrieve your IP address."

def handle_flip_coin():
    result = random.choice(["Heads", "Tails"])
    return f"I flipped a coin — it's {result}!"

def handle_roll_dice():
    result = random.randint(1, 6)
    return f"I rolled a dice — you got {result}!"

def handle_reminder():
    return "Reminder functionality is not set up yet. Try using your phone's alarm for now!"


# ════════════════════════════════════════════════════
#  CORE NLP DISPATCHER
# ════════════════════════════════════════════════════
def handle_command(raw: str) -> str:
    c = raw.lower().strip()

    # 1. Small talk check first (fast path)
    for pattern, responses in SMALL_TALK.items():
        if re.search(pattern, c):
            return random.choice(responses)

    # 2. Confirmed shutdown
    if re.search(r'\bconfirm shutdown\b', c):
        return handle_confirmed_shutdown()

    # 3. Intent matching
    for pattern, intent in INTENTS:
        m = re.search(pattern, c)
        if m:
            if intent == "get_time":       return handle_get_time()
            if intent == "get_date":       return handle_get_date()
            if intent == "joke":           return handle_joke()
            if intent == "open_app":       return handle_open_app(m, c)
            if intent == "close_app":      return handle_close_app(m, c)
            if intent == "set_volume":     return handle_set_volume(m)
            if intent == "volume_up":      return handle_volume_up()
            if intent == "volume_down":    return handle_volume_down()
            if intent == "mute":           return handle_mute()
            if intent == "wikipedia":      return handle_wikipedia(m, c)
            if intent == "calc":           return handle_calc(m, c)
            if intent == "calc_direct":    return handle_calc(m, c)
            if intent == "youtube_search": return handle_youtube(m)
            if intent == "google_search":  return handle_google_search(m)
            if intent == "open_website":   return handle_open_website(m, c)
            if intent == "weather":        return handle_weather()
            if intent == "news":           return handle_news()
            if intent == "screenshot":     return handle_screenshot()
            if intent == "shutdown":       return handle_shutdown()
            if intent == "restart":        return handle_restart()
            if intent == "sleep":          return handle_sleep()
            if intent == "lock":           return handle_lock()
            if intent == "battery":        return handle_battery()
            if intent == "ip_address":     return handle_ip()
            if intent == "flip_coin":      return handle_flip_coin()
            if intent == "roll_dice":      return handle_roll_dice()
            if intent == "reminder":       return handle_reminder()

    # 4. Fallback: echo back intelligently
    return (
        f"I heard you say: \"{raw}\". "
        "I'm still learning! Try asking me to open an app, search Google, "
        "tell a joke, check the time, or do math."
    )


# ════════════════════════════════════════════════════
#  FLASK ROUTES
# ════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400
    user_text = data["text"]
    print(f"[NOVA] ← {user_text}")
    reply = handle_command(user_text)
    print(f"[NOVA] → {reply}")
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
