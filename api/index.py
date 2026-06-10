import os
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')
import math
import json
import random
import datetime
import subprocess
import webbrowser
import urllib.parse

from flask import Flask, render_template, request, jsonify

import requests

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

app = Flask(__name__, template_folder='../templates', static_folder='../public', static_url_path='/')
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
    if key in APPS:
        return f"I'd open {name} for you, but app launching only works when Nova is running locally on your PC — not on the web version."
    return None

def _open_website(url: str, label: str = "") -> str:
    return f"Here's the link you need: {url} — click it to open {label or url}!"

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
    search_url = "https://en.wikipedia.org/w/api.php"
    headers = {
        "User-Agent": "NovaVoiceAssistant/2.0 (nishant@example.com)"
    }
    try:
        # Step 1: Search for the most relevant page title
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "utf8": 1,
            "formatversion": 2
        }
        r = requests.get(search_url, params=search_params, headers=headers, timeout=5)
        r.raise_for_status()
        search_results = r.json().get("query", {}).get("search", [])
        if not search_results:
            return f"I couldn't find any Wikipedia pages matching '{query}'."
        
        # Get the top search result title
        title = search_results[0]["title"]
        
        # Step 2: Fetch a 2-sentence extract of that page
        extract_params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "exsentences": 2,
            "titles": title,
            "formatversion": 2
        }
        r2 = requests.get(search_url, params=extract_params, headers=headers, timeout=5)
        r2.raise_for_status()
        pages = r2.json().get("query", {}).get("pages", [])
        if pages and "extract" in pages[0] and pages[0]["extract"].strip():
            return pages[0]["extract"].strip()
            
    except Exception as e:
        print(f"[WIKI ERROR] {e}")
        
    # Fallback
    url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(query)}"
    return f"Here's the Wikipedia link for '{query}': {url}"

def _get_weather(city: str) -> str:
    url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        data = r.json()
        current = data.get("current_condition", [{}])[0]
        temp = current.get("temp_C", "unknown")
        desc = current.get("weatherDesc", [{}])[0].get("value", "unknown")
        humidity = current.get("humidity", "unknown")
        wind = current.get("windspeedKmph", "unknown")
        
        loc_desc = ""
        nearest_area = data.get("nearest_area", [{}])[0]
        region = nearest_area.get("region", [{}])[0].get("value", "")
        country = nearest_area.get("country", [{}])[0].get("value", "")
        if region:
            loc_desc = f" in {region}, {country}" if not city else f" in {city.capitalize()}"
            
        return f"The weather{loc_desc} is currently {desc} at {temp} degrees Celsius, with {humidity} percent humidity and winds at {wind} kilometers per hour."
    except Exception as e:
        print(f"[WEATHER ERROR] {e}")
        search_city = city or "today"
        return f"I couldn't fetch real-time weather details. Here's a search link instead: https://www.google.com/search?q=weather+{urllib.parse.quote(search_city)}"

def _send_email(to_addr: str, subject: str, body: str) -> str:
    import smtplib
    from email.mime.text import MIMEText
    
    user = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASSWORD")
    server_addr = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    
    if not user or not password:
        return (
            "I cannot send the email because your SMTP credentials are not configured. "
            "Please configure the EMAIL_USER and EMAIL_PASSWORD environment variables."
        )
    
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = user
        msg['To'] = to_addr
        
        server = smtplib.SMTP(server_addr, port)
        server.starttls()
        server.login(user, password)
        server.sendmail(user, [to_addr], msg.as_string())
        server.quit()
        return f"Email sent successfully to {to_addr}!"
    except Exception as e:
        return f"Failed to send email. Error: {e}"

def _get_dictionary(word: str) -> str:
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word.strip())}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 404:
            return f"I couldn't find a dictionary entry for the word '{word}'."
        r.raise_for_status()
        data = r.json()
        meanings = data[0].get("meanings", [])
        if meanings:
            partOfSpeech = meanings[0].get("partOfSpeech", "noun")
            definition = meanings[0].get("definitions", [{}])[0].get("definition", "")
            return f"According to the dictionary, '{word}' is a {partOfSpeech}. Definition: {definition}"
    except Exception as e:
        print(f"[DICTIONARY ERROR] {e}")
    return f"Sorry, I had trouble looking up the definition for '{word}'."

def _get_currency(amount_str: str, from_curr: str, to_curr: str) -> str:
    from_curr = from_curr.upper().strip()
    to_curr = to_curr.upper().strip()
    try:
        amount = float(amount_str)
    except ValueError:
        return "Please specify a valid numeric amount to convert."
        
    url = f"https://open.er-api.com/v6/latest/{from_curr}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        if data.get("result") == "error":
            return f"Unsupported base currency '{from_curr}'."
        rates = data.get("rates", {})
        if to_curr not in rates:
            return f"I couldn't find exchange rates for target currency '{to_curr}'."
        rate = rates[to_curr]
        result = amount * rate
        return f"{amount} {from_curr} is equal to {result:.2f} {to_curr} at a rate of 1 to {rate:.4f}."
    except Exception as e:
        print(f"[CURRENCY ERROR] {e}")
    return "I had trouble fetching currency exchange rates."

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
    
    # Send email
    (r"\b(send email to|email to)\b\s*(\S+)\s*\b(with subject|subject)\b\s*(.+?)\s*\b(and body|body)\b\s*(.+)", "email"),
    
    # Reminders
    (r"\b(remind me to|set reminder to)\b\s*(.+?)\s*\bin\b\s*(\d+)\s*\b(minute|minutes|second|seconds|hour|hours)\b", "reminder"),
    
    # Smart Home status
    (r"\b(turn on|turn off|switch on|switch off|toggle)\b\s*(the)?\s*(kitchen light|living room light|living room ac|kitchen ac|light|ac)\b", "smart_home"),
    (r"\b(set thermostat to|thermostat to|set temperature to)\b\s*.*?(\d+)", "thermostat"),

    # Dictionary API
    (r"\b(define|definition of|meaning of|what is the meaning of)\b\s*(.+)", "dictionary"),
    
    # Currency conversion
    (r"\b(convert)\b\s*(\d+\.?\d*)\s*(\S+)\s*\b(to)\b\s*(\S+)", "currency"),

    # Weather in a city
    (r"\b(weather in|weather of|temperature in|how is the weather in)\b\s*(.+)", "weather_city"),
    # Weather general
    (r"\b(weather|temperature|forecast|how hot|how cold)\b", "weather"),
    
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
    return f"App closing only works when Nova runs locally on your PC."

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
    return f"Here's your YouTube search for {query}: {url}"

def handle_google_search(match):
    query = match.group(2).strip() if match.lastindex and match.lastindex >= 2 else ""
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    return f"Here's your Google search for {query}: {url}"

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
    return f"Here's the link: {target}"

def handle_weather():
    return _get_weather("")

def handle_weather_city(match):
    city = match.group(2).strip()
    return _get_weather(city)

def handle_email(match):
    recipient = match.group(2).strip()
    subject = match.group(4).strip()
    body = match.group(6).strip()
    return _send_email(recipient, subject, body)

def handle_reminder(match):
    task = match.group(2).strip()
    amount = int(match.group(3))
    unit = match.group(4).strip().lower()
    
    if "second" in unit:
        seconds = amount
    elif "minute" in unit:
        seconds = amount * 60
    elif "hour" in unit:
        seconds = amount * 3600
    else:
        seconds = amount
        
    return {
        "reply": f"Setting a reminder to '{task}' in {amount} {unit}.",
        "reminder": {
            "text": task,
            "delaySeconds": seconds
        }
    }

def handle_smart_home(match):
    action = match.group(1).strip().lower()
    device_raw = match.group(3).strip().lower()
    
    device_id = ""
    device_label = device_raw
    
    if "living room light" in device_raw:
        device_id = "living_room_light"
        device_label = "living room light"
    elif "kitchen light" in device_raw or "light" in device_raw:
        device_id = "kitchen_light"
        device_label = "kitchen light"
    elif "living room ac" in device_raw or "ac" in device_raw:
        device_id = "living_room_ac"
        device_label = "living room A C"
    elif "kitchen ac" in device_raw:
        device_id = "kitchen_ac"
        device_label = "kitchen A C"
        
    state = "on"
    if "off" in action:
        state = "off"
    elif "toggle" in action:
        state = "toggle"
        
    return {
        "reply": f"Understood. I have simulated turning {state} the {device_label}.",
        "smart_home": {
            "device": device_id,
            "state": state
        }
    }

def handle_thermostat(match):
    temp = int(match.group(2))
    return {
        "reply": f"Understood. Thermostat target temperature set to {temp} degrees.",
        "smart_home": {
            "device": "thermostat",
            "state": temp
        }
    }

def handle_dictionary(match):
    word = match.group(2).strip()
    return _get_dictionary(word)

def handle_currency(match):
    amount = match.group(2).strip()
    from_curr = match.group(3).strip()
    to_curr = match.group(5).strip()
    return _get_currency(amount, from_curr, to_curr)

def handle_news():
    return "Here's Google News: https://news.google.com — click to open!"

def handle_screenshot():
    return "Screenshot capture only works when Nova runs locally on your Windows PC."

def handle_shutdown():
    return "Shutdown command requires confirmation. Please type 'confirm shutdown' for safety."

def handle_confirmed_shutdown():
    return "Shutdown commands only work when Nova runs locally on your PC."

def handle_restart():
    return "Restart commands only work when Nova runs locally on your PC."

def handle_sleep():
    return "Sleep commands only work when Nova runs locally on your PC."

def handle_lock():
    return "Screen lock only works when Nova runs locally on your PC."

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


# ════════════════════════════════════════════════════
#  CORE NLP DISPATCHER
# ════════════════════════════════════════════════════
def handle_command(raw: str):
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
            
            if intent == "email":          return handle_email(m)
            if intent == "reminder":       return handle_reminder(m)
            if intent == "smart_home":     return handle_smart_home(m)
            if intent == "thermostat":     return handle_thermostat(m)
            if intent == "dictionary":     return handle_dictionary(m)
            if intent == "currency":       return handle_currency(m)
            if intent == "weather_city":   return handle_weather_city(m)
            
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
    print(f"[NOVA] <- {user_text}")
    res = handle_command(user_text)
    print(f"[NOVA] -> {res}")
    if isinstance(res, dict):
        return jsonify(res)
    return jsonify({"reply": res})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)