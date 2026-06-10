import speech_recognition as sr   # converts voice → text
import pyttsx3                     # converts text → voice (offline TTS)
import datetime                    # for time and date commands
import webbrowser                  # to open browser for web searches
import time                        # for small delays
import sys                         # for clean exit
import random                      # for random joke/greeting selection

# Optional: for Wikipedia search (install: pip install wikipedia-api)
try:
    import wikipedia
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    WIKIPEDIA_AVAILABLE = False
 
 
# ─── STEP 3: CONFIGURATION ────────────────────────────────────────────────────
# Centralise all settings here so you can tweak without touching logic
 
ASSISTANT_NAME = "Nova"            # Change to any name you like
USER_NAME      = "Nishant"        # Change to your name
 
# Text-to-Speech settings
TTS_RATE   = 175     # words per minute  (default ~200, lower = slower)
TTS_VOLUME = 1.0     # 0.0 to 1.0
TTS_VOICE  = "female"  # "female" or "male" (picks closest available voice)

# Speech recognition settings
ENERGY_THRESHOLD    = 300   # mic sensitivity  (higher = less sensitive)
PAUSE_THRESHOLD     = 0.8   # seconds of silence before phrase ends
RECOGNITION_TIMEOUT = 5     # seconds to wait for speech to start
PHRASE_TIME_LIMIT   = 10    # max seconds per command
 
# Search engine base URLs
GOOGLE_URL    = "https://www.google.com/search?q="
YOUTUBE_URL   = "https://www.youtube.com/results?search_query="
WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/"
 
 
# ─── STEP 4: TEXT-TO-SPEECH ENGINE SETUP ─────────────────────────────────────
def setup_tts_engine():
    """
    Initialise pyttsx3 and configure voice, rate, and volume.
    pyttsx3 works OFFLINE — no API key needed.
    """
    engine = pyttsx3.init()
 
    # Set speaking rate
    engine.setProperty("rate", TTS_RATE)
 
    # Set volume
    engine.setProperty("volume", TTS_VOLUME)
 
    # Pick a voice (female preferred, falls back to first available)
    voices = engine.getProperty("voices")
    selected_voice = voices[0]  # default fallback
 
    for voice in voices:
        name = voice.name.lower()
        if TTS_VOICE == "female" and any(w in name for w in ["female", "zira", "hazel", "susan", "victoria", "samantha"]):
            selected_voice = voice
            break
        if TTS_VOICE == "male" and any(w in name for w in ["male", "david", "mark", "daniel", "alex"]):
            selected_voice = voice
            break
 
    engine.setProperty("voice", selected_voice.id)
    return engine
 
 
# ─── STEP 5: SPEAK FUNCTION ───────────────────────────────────────────────────
def speak(engine, text):
    """
    Convert text to speech and print it to the console simultaneously.
    engine : pyttsx3 engine instance
    text   : string to speak
    """
    print(f"\n  [{ASSISTANT_NAME}]: {text}")
    engine.say(text)
    engine.runAndWait()
 
 
# ─── STEP 6: LISTEN FUNCTION ──────────────────────────────────────────────────
def listen(recognizer, microphone):
    """
    Capture audio from microphone and convert to text using Google Speech API.
    Falls back gracefully on errors.
 
    Returns: recognised text (str) or None on failure
    """
    print(f"\n  [Listening...] Speak now:")
 
    try:
        with microphone as source:
            # Adjust for ambient noise each time (helps in noisy environments)
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
 
            # Capture audio
            audio = recognizer.listen(
                source,
                timeout=RECOGNITION_TIMEOUT,
                phrase_time_limit=PHRASE_TIME_LIMIT
            )
 
        # Try Google Speech Recognition (requires internet)
        # For offline: use recognizer.recognize_sphinx(audio) after installing PocketSphinx
        text = recognizer.recognize_google(audio, language="en-IN")
        print(f"  [You said]: {text}")
        return text.lower().strip()
 
    except sr.WaitTimeoutError:
        print("  [Timeout] No speech detected.")
        return None
 
    except sr.UnknownValueError:
        print("  [Error] Could not understand audio.")
        return None
 
    except sr.RequestError as e:
        print(f"  [Network Error] Speech API unavailable: {e}")
        print("  [Tip] Check your internet connection. Falling back to text input.")
        return None
 
 
# ─── STEP 7: COMMAND HANDLERS ─────────────────────────────────────────────────
 
JOKES = [
    "Why do Python developers prefer dark mode? Because light attracts bugs!",
    "Why did the Django developer go broke? He used too many free templates!",
    "A SQL query walks into a bar and asks two tables: Can I join you?",
    "Why do Java developers wear glasses? Because they don't C sharp!",
    "What is a computer's favourite snack? Microchips!"
]
 
GREETINGS = [
    f"Hello, {USER_NAME}! Great to see you. How can I help?",
    f"Hey {USER_NAME}! I'm {ASSISTANT_NAME}, your voice assistant. What can I do for you?",
    f"Hi there, {USER_NAME}! Ready to assist. What do you need?"
]
 
 
def handle_greeting():
    return random.choice(GREETINGS)
 
 
def handle_time():
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p")          # e.g. 03:45 PM
    return f"The current time is {time_str}."
 
 
def handle_date():
    now = datetime.datetime.now()
    date_str = now.strftime("%A, %d %B %Y")      # e.g. Tuesday, 09 June 2026
    return f"Today is {date_str}."
 
 
def handle_day():
    day = datetime.datetime.now().strftime("%A")
    weekend = day in ["Saturday", "Sunday"]
    suffix = "Enjoy your weekend!" if weekend else "Have a productive day!"
    return f"Today is {day}. {suffix}"
 
 
def handle_joke():
    return random.choice(JOKES)
 
 
def handle_web_search(engine, query, platform="google"):
    """Open the default browser with a search query."""
    query_encoded = query.replace(" ", "+")
 
    if platform == "youtube":
        url = YOUTUBE_URL + query_encoded
        speak(engine, f"Searching YouTube for {query}.")
    else:
        url = GOOGLE_URL + query_encoded
        speak(engine, f"Searching Google for {query}.")
 
    webbrowser.open(url)
    return None   # already spoke inside this function
 
 
def handle_wikipedia(engine, topic):
    """Fetch a short Wikipedia summary (requires wikipedia package)."""
    if not WIKIPEDIA_AVAILABLE:
        return f"Wikipedia package not installed. Try: pip install wikipedia. I'll search Google instead."
 
    try:
        wikipedia.set_lang("en")
        summary = wikipedia.summary(topic, sentences=2)
        return f"According to Wikipedia: {summary}"
    except wikipedia.exceptions.DisambiguationError as e:
        return f"That topic is ambiguous. Did you mean: {', '.join(e.options[:3])}?"
    except wikipedia.exceptions.PageError:
        return f"I couldn't find a Wikipedia page for {topic}. Trying a Google search instead."
    except Exception:
        return f"Something went wrong fetching Wikipedia. Let me search Google instead."
 
 
def handle_open_website(engine, site):
    """Open a named website directly."""
    sites = {
        "google"   : "https://www.google.com",
        "youtube"  : "https://www.youtube.com",
        "github"   : "https://www.github.com",
        "linkedin" : "https://www.linkedin.com",
        "gmail"    : "https://mail.google.com",
        "maps"     : "https://maps.google.com",
        "stackoverflow" : "https://stackoverflow.com",
    }
    if site in sites:
        speak(engine, f"Opening {site}.")
        webbrowser.open(sites[site])
        return None
    return f"I don't have a shortcut for {site} yet. Try saying 'search for {site}'."
 
 
def handle_help():
    return (
        f"Here's what I can do: "
        f"Tell the time, tell the date, tell jokes, "
        f"search Google or YouTube, open websites like GitHub or LinkedIn, "
        f"look up topics on Wikipedia, "
        f"and have a basic conversation. "
        f"Say 'exit' or 'quit' to stop me."
    )
 
 
# ─── STEP 8: COMMAND PARSER ───────────────────────────────────────────────────
def parse_and_execute(engine, command):
    """
    Match the user's command string to a handler function.
    Returns the response string (or None if already handled inside the function).
    """
    c = command.lower().strip()
 
    # ── Greetings ──
    if any(w in c for w in ["hello", "hi", "hey", "good morning", "good evening",
                              "good afternoon", "good night", "namaste", "wassup"]):
        return handle_greeting()
 
    # ── How are you ──
    if any(p in c for p in ["how are you", "how r u", "how do you do", "you okay"]):
        return f"I'm doing great, {USER_NAME}, thank you for asking! What can I help you with?"
 
    # ── Time ──
    if any(p in c for p in ["what time", "current time", "tell time", "time now", "time please"]):
        return handle_time()
 
    # ── Date ──
    if any(p in c for p in ["what date", "today's date", "current date",
                              "what is the date", "tell me date"]):
        return handle_date()
 
    # ── Day ──
    if any(p in c for p in ["what day", "which day", "day today", "today day"]):
        return handle_day()
 
    # ── Joke ──
    if any(w in c for w in ["joke", "funny", "laugh", "humor", "make me laugh"]):
        return handle_joke()
 
    # ── Wikipedia ──
    if c.startswith("what is") or c.startswith("who is") or c.startswith("tell me about"):
        for prefix in ["what is", "who is", "tell me about"]:
            if c.startswith(prefix):
                topic = c[len(prefix):].strip()
                if topic:
                    return handle_wikipedia(engine, topic)
 
    # ── YouTube search ──
    if "search youtube" in c or "youtube search" in c or "play on youtube" in c:
        for prefix in ["search youtube for", "search youtube", "youtube search for",
                        "youtube search", "play on youtube"]:
            if c.startswith(prefix):
                query = c[len(prefix):].strip()
                if query:
                    handle_web_search(engine, query, platform="youtube")
                    return None
        return "What would you like me to search on YouTube?"
 
    # ── Google search ──
    if any(p in c for p in ["search for", "search about", "google search", "look up", "find me"]):
        for prefix in ["search for", "search about", "google search for",
                        "google search", "look up", "find me"]:
            if c.startswith(prefix):
                query = c[len(prefix):].strip()
                if query:
                    handle_web_search(engine, query, platform="google")
                    return None
        return "What would you like me to search for?"
 
    # ── Open website ──
    if c.startswith("open "):
        site = c[5:].strip().lower()
        return handle_open_website(engine, site)
 
    # ── Your name / identity ──
    if any(p in c for p in ["your name", "who are you", "what are you", "introduce yourself"]):
        return (f"I'm {ASSISTANT_NAME}, your personal voice assistant built in Python "
                f"using SpeechRecognition and pyttsx3. I'm here to make your life easier!")
 
    # ── Help ──
    if any(w in c for w in ["help", "what can you do", "commands", "features", "capabilities"]):
        return handle_help()
 
    # ── Exit ──
    if any(w in c for w in ["exit", "quit", "bye", "goodbye", "stop", "shut down", "see you"]):
        speak(engine, f"Goodbye, {USER_NAME}! Have a great day!")
        sys.exit(0)
 
    # ── Fallback ──
    return (f"I heard '{command}', but I'm not sure how to handle that. "
            f"Try saying 'search for {command}' or say 'help' to see all commands.")
 
 
# ─── STEP 9: TEXT INPUT FALLBACK ──────────────────────────────────────────────
def get_text_input():
    """
    Fallback for environments where microphone is unavailable.
    Reads command from keyboard input.
    """
    try:
        return input(f"\n  [Type command]: ").lower().strip()
    except (EOFError, KeyboardInterrupt):
        return "exit"
 
 
# ─── STEP 10: MAIN LOOP ───────────────────────────────────────────────────────
def main():
    """
    Main assistant loop:
    1. Initialise TTS engine and microphone
    2. Greet the user
    3. Loop: listen → parse → respond → repeat
    4. Exit cleanly on 'exit' command
    """
    print("=" * 60)
    print(f"  {ASSISTANT_NAME} — Voice Assistant")
    print(f"  Python {sys.version.split()[0]}")
    print("=" * 60)
    print("  Starting up... (Ctrl+C to quit at any time)")
    print()
 
    # ── Init TTS ──
    try:
        engine = setup_tts_engine()
    except Exception as e:
        print(f"  [TTS Error] {e}")
        print("  Tip: Install pyttsx3 with: pip install pyttsx3")
        sys.exit(1)
 
    # ── Init microphone ──
    recognizer  = sr.Recognizer()
    recognizer.energy_threshold = ENERGY_THRESHOLD
    recognizer.pause_threshold  = PAUSE_THRESHOLD
 
    use_mic = True
    try:
        microphone = sr.Microphone()
        # Quick test to make sure mic is accessible
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
        print("  Microphone detected and ready.")
    except (OSError, AttributeError) as e:
        print(f"  [Mic Warning] {e}")
        print("  Falling back to text input mode.")
        use_mic = False
        microphone = None
 
    # ── Welcome ──
    speak(engine, f"Hello {USER_NAME}! I'm {ASSISTANT_NAME}, your voice assistant. Say 'help' to see what I can do.")
 
    # ── Main loop ──
    consecutive_errors = 0
    MAX_ERRORS = 5   # switch to text input after this many mic failures
 
    while True:
        try:
            # Get command
            if use_mic and consecutive_errors < MAX_ERRORS:
                command = listen(recognizer, microphone)
            else:
                command = get_text_input()
 
            if not command:
                consecutive_errors += 1
                if consecutive_errors >= MAX_ERRORS:
                    speak(engine, "Having trouble with the microphone. Switching to text input mode.")
                    use_mic = False
                continue
 
            consecutive_errors = 0   # reset on success
 
            # Parse and execute
            response = parse_and_execute(engine, command)
 
            # Speak response (if not already handled inside the command function)
            if response:
                speak(engine, response)
 
            time.sleep(0.3)   # brief pause between commands
 
        except KeyboardInterrupt:
            speak(engine, f"Goodbye, {USER_NAME}!")
            print("\n  Exiting. Bye!")
            break
 
        except Exception as e:
            print(f"  [Unexpected Error] {e}")
            consecutive_errors += 1
 
 
# ─── ENTRY POINT ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
 