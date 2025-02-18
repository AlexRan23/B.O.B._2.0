import os
import subprocess
import pyttsx3
import speech_recognition as sr
import psutil
import requests
import logging
import json
import sys
from time import sleep
from threading import Thread, Event
import webbrowser

# Initialize logging
logging.basicConfig(
    filename="bob3.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Load configuration from JSON file
def load_config():
    """Load and validate the configuration from the JSON file."""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        
        # Validate required configuration keys
        required_keys = ["APPLICATIONS", "CUSTOM_APPS", "WEB_URLS", "SELF_IMPROVE_URL"]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required configuration key: {key}")
        
        logging.info("Configuration loaded successfully.")
        return config
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        raise

config = load_config()

APPLICATIONS = config.get("APPLICATIONS", {})
CUSTOM_APPS = config.get("CUSTOM_APPS", {})
WEB_URLS = config.get("WEB_URLS", {})
SELF_IMPROVE_URL = config.get("SELF_IMPROVE_URL", "")

# Initialize TTS engine
engine = pyttsx3.init()
engine.setProperty("rate", 150)  # Adjust speech rate
engine.setProperty("voice", "english")  # Set voice (adjust as needed)

# Global flag for scheduled tasks
RUN_SCHEDULED_TASKS = Event()
RUN_SCHEDULED_TASKS.set()  # Set the event to allow tasks to run

def speak(text):
    """Speak the given text using TTS."""
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        logging.error(f"Error in TTS: {e}")
        print(f"Error in TTS: {e}")

def manage_application(action, app_name):
    """Open, close, or check the status of an app."""
    process_name = APPLICATIONS.get(app_name) or CUSTOM_APPS.get(app_name)
    if not process_name:
        return f"Unknown application '{app_name}'"

    try:
        if action == "open":
            subprocess.Popen([process_name], shell=True)
            speak(f"Opening {app_name}.")
            return f"Opening {app_name}."
        elif action == "close":
            os.system(f"taskkill /f /im {process_name}")
            speak(f"Closing {app_name}.")
            return f"Closing {app_name}."
        elif action == "status":
            for proc in psutil.process_iter(['name']):
                if process_name.lower() in proc.info['name'].lower():
                    speak(f"{app_name.capitalize()} is running.")
                    return f"{app_name.capitalize()} is running."
            speak(f"{app_name.capitalize()} is not running.")
            return f"{app_name.capitalize()} is not running."
        else:
            speak(f"Unknown action '{action}' for application '{app_name}'")
            return f"Unknown action '{action}' for application '{app_name}'"
    except Exception as e:
        logging.error(f"Error managing application '{app_name}': {e}")
        speak(f"Failed to {action} {app_name}.")
        return f"Failed to {action} {app_name}."

def open_website(url_key):
    """Open a website in the default browser."""
    if url_key in WEB_URLS:
        webbrowser.open(WEB_URLS[url_key])
        speak(f"Opening {url_key}.")
        return f"Opening {url_key}."
    speak(f"Unknown website '{url_key}'.")
    return f"Unknown website '{url_key}'."

def self_improve():
    """Automatically fetch improvements and apply them."""
    if not SELF_IMPROVE_URL:
        speak("Self-improvement URL is not configured.")
        return "Self-improvement URL is not configured."

    try:
        # Fetch the new script from the URL
        response = requests.get(SELF_IMPROVE_URL)
        if response.status_code == 200:
            new_code = response.text

            # Backup the current script
            try:
                with open("Bob3.py", "r") as f:
                    current_code = f.read()

                # Write the new script
                with open("Bob3.py", "w") as f:
                    f.write(new_code)

                # Restart the assistant with the new script
                speak("B.O.B._2.0 has improved itself with the latest code! Restarting...")
                sleep(2)
                os.execv(sys.executable, ['python'] + sys.argv)  # Restart the script
                return "The assistant has been updated and restarted."
            except Exception as e:
                logging.error(f"Error during file operations: {e}")
                speak("Failed to apply self-improvement due to a file error.")
                return "Failed to apply self-improvement due to a file error."
        else:
            speak(f"Failed to fetch the update. HTTP Status Code: {response.status_code}")
            return f"Failed to fetch the update. HTTP Status Code: {response.status_code}"

    except Exception as e:
        logging.error(f"Error during self-improvement process: {e}")
        speak("Failed to apply self-improvement.")
        return "Failed to apply self-improvement."

def listen():
    """Listen for voice commands."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text.lower()
        except sr.UnknownValueError:
            logging.warning("Speech recognition could not understand audio.")
            speak("Sorry, I didn't catch that. Could you repeat?")
            return ""
        except sr.RequestError as e:
            logging.error(f"Could not request results from Google Speech Recognition service: {e}")
            speak("There was an issue with speech recognition service. Please try again.")
            return ""
        except Exception as e:
            logging.error(f"Unexpected error in listen function: {e}")
            speak("An unexpected error occurred. Please try again.")
            return ""

def handle_command(command):
    """Handle user commands."""
    if "open" in command:
        for app in APPLICATIONS:
            if app in command:
                return manage_application("open", app)
        for app in CUSTOM_APPS:
            if app in command:
                return manage_application("open", app)
        for url in WEB_URLS:
            if url in command:
                return open_website(url)
        return "Application or website not recognized."
    elif "close" in command:
        for app in APPLICATIONS:
            if app in command:
                return manage_application("close", app)
        for app in CUSTOM_APPS:
            if app in command:
                return manage_application("close", app)
        return "Application not recognized."
    elif "status" in command:
        for app in APPLICATIONS:
            if app in command:
                return manage_application("status", app)
        for app in CUSTOM_APPS:
            if app in command:
                return manage_application("status", app)
        return "Application not recognized."
    elif "self improve" in command:
        return self_improve()
    elif "exit" in command:
        global RUN_SCHEDULED_TASKS
        RUN_SCHEDULED_TASKS.clea
