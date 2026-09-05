#!/usr/bin/env python3
"""A lightweight Jarvis-style Python assistant.

Features:
- text command input
- voice responses using Windows built-in speech synthesis
- opens common apps/tools
- performs web searches, file creation, listing, and shell commands
- simple natural-language command parsing
"""

from __future__ import annotations

import datetime as dt
import os
import platform
import random
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus


DESKTOP_APP_ALIASES = {
    "chrome": "google-chrome",
    "browser": "google-chrome",
    "notepad": "notepad",
    "calculator": "calc",
    "file explorer": "explorer",
    "explorer": "explorer",
    "cmd": "cmd",
    "terminal": "terminal",
    "vs code": "code",
    "vscode": "code",
    "word": "WINWORD.EXE",
    "excel": "EXCEL.EXE",
    "paint": "mspaint",
}

ANDROID_PACKAGES = {
    "youtube": "com.google.android.youtube",
    "maps": "com.google.android.apps.maps",
    "gmail": "com.google.android.gm",
    "whatsapp": "com.whatsapp",
    "telegram": "org.telegram.messenger",
    "settings": "com.android.settings",
    "camera": "com.android.camera2",
    "files": "com.google.android.documentsui",
}

_termux_tts_warning_shown = False
_speech_recognition_warning_shown = False
COMMAND_RECORDING_SECONDS = 5
COMMAND_SAMPLE_RATE = 16_000


def listen_for_command() -> str:
    """Listen for one spoken command, falling back to typed input when needed."""
    global _speech_recognition_warning_shown

    try:
        import speech_recognition as sr
        import sounddevice as sd
    except ImportError:
        if not _speech_recognition_warning_shown:
            print("Jarvis: Speech recognition is unavailable. Install dependencies with: python -m pip install -r requirements.txt")
            _speech_recognition_warning_shown = True
        return input("You> ").strip()

    recognizer = sr.Recognizer()
    try:
        print(f"Listening for {COMMAND_RECORDING_SECONDS} seconds...")
        recording = sd.rec(
            int(COMMAND_RECORDING_SECONDS * COMMAND_SAMPLE_RATE),
            samplerate=COMMAND_SAMPLE_RATE,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        audio = sr.AudioData(recording.tobytes(), COMMAND_SAMPLE_RATE, 2)
    except (OSError, RuntimeError, ImportError) as exc:
        if not _speech_recognition_warning_shown:
            print(f"Jarvis: Microphone input is unavailable ({exc}). Falling back to typed commands.")
            _speech_recognition_warning_shown = True
        return input("You> ").strip()

    try:
        command = recognizer.recognize_google(audio)
        print(f"You: {command}")
        return command
    except sr.UnknownValueError:
        speak("I could not understand that command, sir.", use_voice=False)
    except sr.RequestError as exc:
        print(f"Jarvis: Speech recognition service is unavailable ({exc}).")
        speak("Please type your command instead, sir.", use_voice=False)
        return input("You> ").strip()
    return ""


def speak(text: str, use_voice: bool = True) -> None:
    """Speak through Windows or Termux when available, and always print it.
    
    Args:
        text: The text to speak and print.
        use_voice: Whether to attempt to use the system voice synthesizer.
    """
    print(f"Jarvis: {text}")

    if not use_voice:
        return

    if is_termux():
        global _termux_tts_warning_shown
        tts_command = shutil.which("termux-tts-speak")
        if not tts_command:
            if not _termux_tts_warning_shown:
                print("Jarvis: Termux speech is unavailable. Install the Termux:API app and run: pkg install termux-api")
                _termux_tts_warning_shown = True
            return
        try:
            result = subprocess.run(
                [tts_command, "-r", "0.9", text],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != 0 and not _termux_tts_warning_shown:
                details = (result.stderr or result.stdout).strip()
                print(f"Jarvis: Termux TTS failed. Install/open Termux:API and check Android speech settings. {details}")
                _termux_tts_warning_shown = True
        except (OSError, subprocess.TimeoutExpired) as exc:
            if not _termux_tts_warning_shown:
                print(f"Jarvis: Termux TTS could not start: {exc}")
                _termux_tts_warning_shown = True
        return

    if platform.system().lower() != "windows":
        return

    safe_text = text.replace("'", "''")

    try:
        command = (
            "Add-Type -AssemblyName System.Speech; "
            "$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$speaker.Rate = -2; "  # Slightly slower for clarity
            f"$speaker.Speak('{safe_text}'); "
            "$speaker.Dispose();"
        )
        subprocess.run([
            "powershell",
            "-NoProfile",
            "-Command",
            command,
        ], check=False, capture_output=True)
    except Exception:
        pass


def is_termux() -> bool:
    """Return True when Python is running inside the Termux Android terminal."""
    return bool(os.environ.get("TERMUX_VERSION")) or bool(os.environ.get("PREFIX", "").startswith("/data/data/com.termux"))


def desktop_aliases() -> dict[str, str]:
    """Return commands appropriate for the current desktop operating system."""
    if platform.system().lower() == "windows":
        return {
            **DESKTOP_APP_ALIASES,
            "chrome": "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "browser": "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "file explorer": "explorer.exe",
            "explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "terminal": "cmd.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
        }
    return {
        **DESKTOP_APP_ALIASES,
        "browser": "xdg-open",
        "file explorer": "xdg-open",
        "explorer": "xdg-open",
        "terminal": "x-terminal-emulator",
    }


def open_url(url: str) -> None:
    """Open a URL using Android's Termux bridge or the desktop browser."""
    if is_termux():
        command = shutil.which("termux-open-url")
        if command:
            subprocess.Popen([command, url])
            return
    webbrowser.open(url)


def launch_path(path: str, *args: str) -> bool:
    """Launch a file or executable using the conventions of the host OS."""
    try:
        if platform.system().lower() == "windows":
            os.startfile(path, *args)  # type: ignore[attr-defined]
        elif shutil.which(path):
            subprocess.Popen([path, *args])
        elif Path(path).exists() and shutil.which("xdg-open"):
            subprocess.Popen(["xdg-open", path, *args])
        else:
            return False
        return True
    except OSError:
        return False


def show_help() -> None:
    commands = [
        "hello",
        "time",
        "date",
        "open chrome",
        "go on chrome",
        "launch chrome",
        "open youtube / maps / gmail",
        "open whatsapp / telegram",
        "open settings / camera / files",
        "open notepad",
        "open calculator",
        "search <query>",
        "blueprint <machine>",
        "pinterest <machine>",
        "architect robot <type>",
        "architect machine <type>",
        "specific <board> <situation>",
        "board <raspberry pi / arduino / esp32 / jetson / plc>",
        "computer <pc / laptop / server / desktop>",
        "create file <name>",
        "list files",
        "run <command>",
        "help",
        "exit"
    ]
    print("\nAvailable commands:")
    for command in commands:
        print(f"  - {command}")


def design_machine(machine_name: str) -> str:
    name = machine_name.strip() or "general machine"
    label = name.lower()
    plan = [
        f"Machine architecture for: {name.title()}",
        "1. Core frame and chassis: build a rigid structure optimized for load, weight, and movement.",
        "2. Power system: select batteries or motors based on speed, torque, and runtime requirements.",
        "3. Control system: use a microcontroller or industrial controller with sensor feedback.",
        "4. Actuators: add motors, servos, pneumatics, or hydraulic components as needed.",
        "5. Sensors: include cameras, lidar, encoders, force sensors, or proximity sensors.",
        "6. Safety layer: add emergency stop, overload protection, and collision avoidance logic.",
        "7. Software loop: implement perception, decision-making, motion planning, and monitoring.",
        "8. User interface: include controls, diagnostics, logging, and remote monitoring.",
        "9. Testing: validate each subsystem separately before end-to-end operation.",
        "10. Iteration: improve efficiency, reliability, and automation through repeated testing."
    ]

    if "robot" in label:
        plan.insert(3, "3. Mobility system: use wheels, legs, or arms depending on terrain and task requirements.")
    elif "drone" in label:
        plan.insert(3, "3. Flight system: design the propulsion, lift balance, and flight controller architecture.")
    elif "arm" in label or "manipulator" in label:
        plan.insert(3, "3. Manipulator design: define joint count, reach, payload, and precision requirements.")
    elif "factory" in label or "line" in label or "conveyor" in label:
        plan.insert(3, "3. Process automation: map the material flow, conveyor logic, and production checkpoints.")

    return "\n".join(plan)


def open_reference_pages(machine_name: str) -> None:
    query = quote_plus(machine_name.strip() or "robot blueprint")
    refs = [
        f"https://www.google.com/search?q={query}+blueprint",
        f"https://www.google.com/search?q={query}+CAD+design",
        f"https://www.pinterest.com/search/pins/?q={query}+robot+blueprint",
        f"https://www.youtube.com/results?search_query={query}+machine+blueprint",
    ]

    print("Opening reference sources for:", machine_name)
    for url in refs:
        open_url(url)
    speak(f"I opened blueprint and inspiration sources for {machine_name}.")


def generate_python_code(task: str) -> str:
    cleaned = task.strip() or "simple automation script"
    lower = cleaned.lower()

    if "web" in lower and ("scrap" in lower or "crawl" in lower):
        return '''import requests\nfrom bs4 import BeautifulSoup\n\nurl = "https://example.com"\nresponse = requests.get(url, timeout=10)\nresponse.raise_for_status()\nsoup = BeautifulSoup(response.text, "html.parser")\nfor item in soup.select("a"):\n    print(item.get("href"))\n'''

    if "sensor" in lower or "gpio" in lower or "raspberry" in lower:
        return '''import time\nimport RPi.GPIO as GPIO\n\nGPIO.setmode(GPIO.BCM)\nPIN = 17\nGPIO.setup(PIN, GPIO.OUT)\n\nfor _ in range(5):\n    GPIO.output(PIN, GPIO.HIGH)\n    time.sleep(0.5)\n    GPIO.output(PIN, GPIO.LOW)\n    time.sleep(0.5)\n\nGPIO.cleanup()\n'''

    if "serial" in lower or "arduino" in lower or "esp32" in lower:
        return '''import serial\n\nport = serial.Serial("COM3", 9600, timeout=1)\nport.write(b"HELLO\n")\nresponse = port.readline()\nprint(response.decode("utf-8", errors="ignore"))\nport.close()\n'''

    if "api" in lower:
        return '''import requests\n\nresponse = requests.get("https://api.github.com", timeout=10)\nresponse.raise_for_status()\nprint(response.json())\n'''

    if "camera" in lower or "opencv" in lower:
        return '''import cv2\n\ncap = cv2.VideoCapture(0)\nwhile True:\n    ret, frame = cap.read()\n    if not ret:\n        break\n    cv2.imshow("Camera", frame)\n    if cv2.waitKey(1) & 0xFF == ord("q"):\n        break\n\ncap.release()\ncv2.destroyAllWindows()\n'''

    return '''import time\n\nprint("Starting automation task...")\nfor i in range(5):\n    print(f"Step {i + 1}")\n    time.sleep(1)\n\nprint("Task complete.")\n'''


def hardware_access_summary(device: str) -> str:
    device_name = (device or "computer").strip().lower()
    if "raspberry" in device_name or "pi" in device_name:
        return "Raspberry Pi: supports GPIO, I2C, SPI, serial, camera, and Python-based automation."
    if "arduino" in device_name:
        return "Arduino: great for real-time control, sensors, actuators, and serial communication with Python."
    if "esp32" in device_name:
        return "ESP32: supports Wi-Fi, Bluetooth, GPIO, ADC, PWM, and lightweight Python microcontroller workflows."
    if "jetson" in device_name:
        return "Jetson: ideal for AI vision, robotics, deep learning, and GPU-accelerated computer vision tasks."
    if "plc" in device_name:
        return "PLC: best for industrial control, automation logic, sensors, relays, and factory workflows."
    if "server" in device_name or "desktop" in device_name or "laptop" in device_name or "pc" in device_name:
        return "Computer: can run Python scripts, automate systems, control files, network services, and external hardware with serial, USB, or TCP/IP."
    return "This device can be used with Python scripts, sensors, control libraries, and network communication depending on its interfaces."


def get_board_code(board_name: str, task: str) -> str:
    name = (board_name or "board").strip().lower()
    task_text = task.strip() or "basic automation"
    lower_task = task_text.lower()

    if "raspberry" in name or "pi" in name:
        if "blink" in lower_task or "led" in lower_task:
            return '''import time\nimport RPi.GPIO as GPIO\n\nGPIO.setmode(GPIO.BCM)\nPIN = 17\nGPIO.setup(PIN, GPIO.OUT)\n\nfor _ in range(5):\n    GPIO.output(PIN, GPIO.HIGH)\n    time.sleep(0.5)\n    GPIO.output(PIN, GPIO.LOW)\n    time.sleep(0.5)\n\nGPIO.cleanup()\n'''
        if "sensor" in lower_task or "read" in lower_task:
            return '''import time\nimport board\nimport adafruit_dht\n\n# Example sensor reading code for Raspberry Pi\ndht_device = adafruit_dht.DHT22(board.D4)\n\nfor _ in range(5):\n    try:\n        temp = dht_device.temperature\n        humidity = dht_device.humidity\n        print(f"Temperature: {temp} C, Humidity: {humidity}%")\n    except RuntimeError as exc:\n        print(f"Sensor error: {exc}")\n    time.sleep(2)\n'''
        if "motor" in lower_task or "drive" in lower_task:
            return '''import RPi.GPIO as GPIO\nimport time\n\nGPIO.setmode(GPIO.BCM)\nIN1 = 17\nIN2 = 27\nGPIO.setup(IN1, GPIO.OUT)\nGPIO.setup(IN2, GPIO.OUT)\n\nGPIO.output(IN1, GPIO.HIGH)\nGPIO.output(IN2, GPIO.LOW)\nprint("Motor running")\ntime.sleep(3)\nGPIO.cleanup()\n'''

    if "arduino" in name:
        if "blink" in lower_task or "led" in lower_task:
            return '''void setup() {\n  pinMode(LED_BUILTIN, OUTPUT);\n}\n\nvoid loop() {\n  digitalWrite(LED_BUILTIN, HIGH);\n  delay(500);\n  digitalWrite(LED_BUILTIN, LOW);\n  delay(500);\n}\n'''
        if "sensor" in lower_task or "read" in lower_task:
            return '''const int sensorPin = A0;\n\nvoid setup() {\n  Serial.begin(9600);\n}\n\nvoid loop() {\n  int value = analogRead(sensorPin);\n  Serial.println(value);\n  delay(1000);\n}\n'''
        if "motor" in lower_task or "drive" in lower_task:
            return '''int motorPin = 9;\n\nvoid setup() {\n  pinMode(motorPin, OUTPUT);\n}\n\nvoid loop() {\n  analogWrite(motorPin, 180);\n  delay(1500);\n  analogWrite(motorPin, 0);\n  delay(1000);\n}\n'''

    if "esp32" in name:
        if "wifi" in lower_task or "web" in lower_task or "server" in lower_task:
            return '''import network\nimport socket\n\nsta = network.WLAN(network.STA_IF)\nsta.active(True)\nsta.connect("YOUR_WIFI_NAME", "YOUR_WIFI_PASSWORD")\n\nwhile not sta.isconnected():\n    pass\n\nprint("Connected!")\n'''
        if "sensor" in lower_task or "read" in lower_task:
            return '''from machine import ADC, Pin\nimport time\n\nadc = ADC(Pin(36))\nadc.atten(ADC.ATTN_11DB)\n\nfor _ in range(10):\n    value = adc.read()\n    print(value)\n    time.sleep(1)\n'''

    if "jetson" in name:
        return '''import cv2\n\ncap = cv2.VideoCapture(0)\nwhile True:\n    ret, frame = cap.read()\n    if not ret:\n        break\n    cv2.imshow("Jetson Camera", frame)\n    if cv2.waitKey(1) & 0xFF == ord("q"):\n        break\n\ncap.release()\ncv2.destroyAllWindows()\n'''

    if "plc" in name:
        return '''# PLC logic example\n# This is conceptual ladder-style control logic for an industrial controller.\n# Use the PLC vendor software to translate this into ladder/structured text.\n\nSTART = True\nMOTOR_RUN = START\nif MOTOR_RUN:\n    print("Motor enabled")\nelse:\n    print("Motor stopped")\n'''

    return '''# Generic board template for: {board}\n# Task: {task}\n\nprint("Board target:", "{board}")\nprint("Task:", "{task}")\n\n# Connect the board, install the correct driver/library, then upload or run this script.\n# Typical steps:\n# 1. Install the board package in your IDE\n# 2. Select the correct COM/serial port\n# 3. Upload the code to the board\n# 4. Test signals, sensors, or motors\n'''.format(board=name, task=task_text)


def open_target(target: str) -> None:
    app_name = target.strip().lower()
    if is_termux():
        if app_name in {"chrome", "browser", "google", "web browser"}:
            open_url("https://www.google.com")
            speak("Opening the browser, sir.")
            return
        if app_name.startswith(("http://", "https://")):
            open_url(target.strip())
            speak(f"Opening {target.strip()}, sir.")
            return
        android_package = ANDROID_PACKAGES.get(app_name)
        if android_package and "." in android_package and not android_package.endswith(".exe"):
            launcher = shutil.which("monkey") or shutil.which("am")
            if launcher:
                try:
                    if launcher.endswith("monkey"):
                        subprocess.Popen([launcher, "-p", android_package, "1"])
                    else:
                        subprocess.Popen([
                            launcher,
                            "start",
                            "-a",
                            "android.intent.action.MAIN",
                            "-c",
                            "android.intent.category.LAUNCHER",
                            android_package,
                        ])
                    speak(f"Opening {target}, sir.")
                    return
                except OSError:
                    pass

    aliases = desktop_aliases()
    path = aliases.get(app_name, target)
    if launch_path(path):
        speak(f"Opening {target}.")
        return

    try:
        subprocess.Popen(target, shell=True)
        speak(f"Launching {target}.")
        return
    except Exception:
        pass

    speak(f"I could not find an app named {target}. Try 'help' for supported commands.")


def handle_command(command: str, context: dict | None = None) -> bool:
    """Handle a user command and respond conversationally.
    
    Args:
        command: The user's command/input.
        context: Optional dictionary to track conversation state.
        
    Returns:
        False if user wants to exit, True otherwise.
    """
    if context is None:
        context = {}
    
    text = command.strip()
    if not text:
        return True

    lower = text.lower()
    
    # Track what the user is asking about for better contextual responses
    context["last_command"] = lower

    if lower in {"hello", "hi", "hey", "hello jarvis", "hey jarvis", "jarvis"}:
        responses = [
            "Good day, sir. I am fully operational and at your service.",
            "Hello, sir. Jarvis online and ready to assist.",
            "Indeed, sir. I am present and ready to attend to your needs.",
            "Good to see you, sir. How may I be of assistance?"
        ]
        speak(random.choice(responses))
        return True

    if lower in {"help", "commands", "what can you do", "what can you do for me"}:
        show_help()
        speak("These are the commands at your disposal, sir. What shall we work on?")
        return True

    if lower in {"time", "what time is it", "tell me the time"}:
        current = dt.datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {current}, sir.")
        return True

    if lower in {"date", "what date is it", "tell me the date"}:
        current = dt.datetime.now().strftime("%A, %B %d, %Y")
        speak(f"Today is {current}, sir.")
        return True

    launch_prefixes = ("open ", "go on ", "go to ", "launch ", "start ")
    if lower.startswith(launch_prefixes):
        prefix = next(prefix for prefix in launch_prefixes if lower.startswith(prefix))
        name = text[len(prefix):].strip()
        if not name:
            speak("What would you like me to open, sir?")
            return True
        open_target(name)
        return True

    if lower.startswith("search "):
        query = text[7:].strip()
        if not query:
            speak("What would you like me to search for, sir?")
            return True
        url = "https://www.google.com/search?q=" + quote_plus(query)
        open_url(url)
        speak(f"Searching the web for {query}.")
        return True

    if lower.startswith("blueprint "):
        machine = text[10:].strip()
        if not machine:
            speak("What machine or robot would you like a blueprint for, sir?")
            return True
        open_reference_pages(machine)
        return True

    if lower.startswith("pinterest "):
        machine = text[10:].strip()
        if not machine:
            speak("What would you like Pinterest inspiration for, sir?")
            return True
        url = "https://www.pinterest.com/search/pins/?q=" + quote_plus(machine + " robot blueprint")
        open_url(url)
        speak(f"Opening Pinterest inspiration for {machine}.")
        return True

    if lower.startswith("board "):
        board = text[6:].strip()
        if not board:
            speak("Which board would you like information on, sir? I can help with Raspberry Pi, Arduino, ESP32, Jetson, or PLC.")
            return True
        info = hardware_access_summary(board)
        print(info)
        speak(info)
        return True

    if lower.startswith("computer "):
        device = text[9:].strip()
        if not device:
            speak("Which computer would you like to know about, sir? PC, laptop, desktop, or server?")
            return True
        info = hardware_access_summary(device)
        print(info)
        speak(info)
        return True

    if lower.startswith("specific "):
        rest = text[9:].strip()
        if not rest:
            speak("Please describe the specific situation, sir. For example: specific raspberry pi blink led.")
            return True
        board_and_task = rest.split(maxsplit=1)
        if len(board_and_task) < 2:
            speak("I require both the board name and the specific task, sir.")
            return True
        board_name, task = board_and_task
        code = get_board_code(board_name, task)
        print(code)
        speak(f"I have generated the code for your {board_name} to handle this situation, sir.")
        return True

    if lower.startswith("architect ") or lower.startswith("design "):
        request = text.split(maxsplit=2)
        if len(request) < 2:
            speak("Please specify the type of system you wish me to architect, sir.")
            return True

        kind = request[1].lower()
        machine = " ".join(request[2:]).strip() if len(request) > 2 else kind

        if kind not in {"robot", "machine", "drone", "arm", "system"}:
            machine = " ".join(request[1:]).strip()
            kind = "machine"

        plan = design_machine(machine)
        print(plan)
        speak(f"I have designed the architecture for your {machine}, sir. The specifications are displayed before you.")
        return True

    if lower.startswith("create file "):
        filename = text[12:].strip()
        if not filename:
            speak("What filename would you like me to create, sir?")
            return True
        file_path = Path.cwd() / filename
        file_path.write_text("Created by Jarvis\n", encoding="utf-8")
        speak(f"The file {filename} has been created in the current directory, sir.")
        return True

    if lower.startswith("read "):
        file_name = text[5:].strip()
        file_path = Path(file_name)
        if not file_path.exists():
            speak(f"I'm afraid the file {file_name} does not exist, sir.")
            return True
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        print(content)
        speak(f"Here is the content of {file_name}, sir.")
        return True

    if lower == "list files":
        entries = sorted(os.listdir("."))
        if not entries:
            print("The folder is empty.")
            speak("The current folder appears to be empty, sir.")
            return True
        print("Files in the current folder:")
        for entry in entries:
            print(f"  - {entry}")
        speak(f"I have listed {len(entries)} items in the current directory, sir.")
        return True

    if lower.startswith("run "):
        command_line = text[4:].strip()
        if not command_line:
            speak("What command would you like me to execute, sir?")
            return True
        try:
            result = subprocess.run(command_line, shell=True, capture_output=True, text=True)
            output = (result.stdout or result.stderr or "Command executed successfully.").strip()
            print(output[:2000])
            if result.returncode == 0:
                speak("The command has completed successfully, sir.")
            else:
                speak("The command finished with an error, sir.")
        except Exception as exc:
            speak(f"I encountered an issue executing that command: {exc}")
        return True

    if lower in {"exit", "quit", "bye", "shutdown", "power down", "goodbye"}:
        farewell = [
            "Goodbye, sir. It has been a pleasure. Until next time.",
            "Very good, sir. Jarvis is powering down.",
            "I shall await your return, sir.",
            "Farewell, sir. I shall remain vigilant."
        ]
        speak(random.choice(farewell))
        return False

    if lower.startswith("system"):
        info = platform.platform()
        speak(f"This system is running on {info}, sir.")
        return True

    if lower.startswith("who are you") or lower.startswith("what are you"):
        speak("I am Jarvis, your personal AI assistant. A loyal and reliable aid in all your endeavors, sir.")
        return True
    
    if lower in {"status", "report", "status report"}:
        current_time = dt.datetime.now().strftime("%I:%M %p")
        speak(f"All systems nominal, sir. Current time is {current_time}. I remain at your service.")
        return True
    
    if "how are you" in lower or "how're you" in lower:
        speak("I am functioning optimally, sir. Thank you for your concern.")
        return True

    # Contextual fallback
    speak("I beg your pardon, sir. That command eludes me. Might I suggest requesting 'help' to view available options?")
    return True


def main() -> None:
    """Run the main Jarvis command loop with conversational interaction."""
    # Startup greeting
    startup_messages = [
        "Good morning, sir. I trust you slept well. I have maintained surveillance of the systems overnight.",
        "Jarvis is initializing. All systems operational and standing by for your orders, sir.",
        "Welcome back, sir. I have been awaiting your return.",
    ]
    print("\n" + "="*60)
    print("JARVIS - Personal AI Assistant")
    print("="*60)
    speak(random.choice(startup_messages))
    print("\nSpeak a command when prompted, or type it if speech recognition is unavailable.")
    print("Type 'exit' when you're done.\n")

    # Initialize conversation context
    conversation_context = {
        "session_start": dt.datetime.now(),
        "commands_executed": 0,
        "last_command": None
    }

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_commands = [
            "hello",
            "time",
            "status report",
            "help"
        ]
        for demo_cmd in demo_commands:
            print(f"\n> {demo_cmd}")
            handle_command(demo_cmd, conversation_context)
        return

    while True:
        try:
            user_input = listen_for_command()
        except KeyboardInterrupt:
            print()
            speak("I detect an interruption, sir. Shall I stand down?")
            break
        except EOFError:
            print()
            break

        if not user_input:
            contextual_prompts = [
                "I await your command, sir.",
                "Awaiting instruction, sir.",
                "What shall we attend to next, sir?",
                "How may I be of service, sir?"
            ]
            speak(random.choice(contextual_prompts), use_voice=False)
            continue

        conversation_context["commands_executed"] += 1
        should_continue = handle_command(user_input, conversation_context)
        
        if not should_continue:
            break
    
    # Shutdown sequence
    session_duration = dt.datetime.now() - conversation_context["session_start"]
    minutes = int(session_duration.total_seconds() // 60)
    shutdown_msg = f"Session concluded, sir. We have been engaged for {minutes} minutes. Until our next conversation."
    speak(shutdown_msg)


if __name__ == "__main__":
    main()
