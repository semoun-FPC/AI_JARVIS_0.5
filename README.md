# Jarvis AI Assistant

A sophisticated, conversational AI assistant inspired by Iron Man's JARVIS. Interact naturally with your personal assistant in VS Code.

## Features
- **Conversational dialogue**: Natural, context-aware responses that feel like talking to Iron Man's JARVIS
- **Speech recognition and voice output**: Speak commands through your microphone, or type them as a fallback; Windows Speech or Termux:API can speak replies
- **Smart responses**: Varied, contextual replies that adapt to your interaction style
- **Session tracking**: Maintains conversation context and tracks command history
- **Personal tasks**: Open apps, search the web, create and read files
- **System control**: Run shell commands, check system information
- **Hardware support**: Design machines, find blueprints, generate board-specific code
- **Multi-turn interaction**: Responsive follow-up prompts and clarifying questions

## Run it

```bash
python jarvis.py
```

You'll see a stylized greeting and can then speak commands naturally. Typed commands remain available when speech recognition is unavailable. Voice output is optional: Windows uses PowerShell speech, Termux uses Termux:API, and Linux remains text-only unless you add your own speech tool.

Install the speech recognition dependencies with:

```bash
python -m pip install -r requirements.txt
```

The first spoken command records for five seconds. Recognition uses Google's speech service and requires an internet connection. Microphone capture uses `sounddevice`, which works with modern VS Code Python environments without PyAudio. If the microphone, package, or service is unavailable, Jarvis falls back to typed input.

On Linux, `open browser` and `open file explorer` use `xdg-open`. Install the desktop command-line helpers provided by your distribution if those commands are unavailable. `open vs code` uses the `code` command when VS Code is installed.

## Run in Termux

Install the Termux:API companion application from the same source as Termux if you want spoken replies, then run these commands inside Termux:

```bash
pkg update
pkg install python termux-api
termux-setup-storage
python jarvis.py
```

Commands are entered at the text prompt. If Termux:API is installed, Jarvis uses `termux-tts-speak` for spoken replies; otherwise it continues in text mode.

On Termux, `open chrome` opens the Android default browser through `termux-open-url`; it does not require Chrome to be installed.

Termux app commands such as `open youtube`, `open maps`, and `open settings` use Android's launch bridge when `monkey` or `am` is available. They require the corresponding Android app to be installed.

## Demo mode

```bash
python jarvis.py --demo
```

Runs through a quick demonstration of core capabilities.

## Conversation Style

Jarvis responds like a sophisticated British AI assistant. Refer to him as "sir" or just speak naturally:

- "Hello" → Gets a varied greeting
- "What time is it?" → Receives the current time with context
- "Status report" → Gets a system status summary
- "Help" → Sees all available commands with contextual follow-ups
- Blank input → Gets a contextual prompt asking what to do next

## Example Commands

### Information & Status
- `hello` / `hi` / `hey`
- `time` / `date` / `status report`
- `help` / `commands`
- `who are you`

### Apps & Web
- `open chrome` / `open notepad` / `open calculator`
- `search python tutorials`
- `blueprint [machine name]`
- `pinterest [machine name]`

### File Management
- `create file notes.txt`
- `read notes.txt`
- `list files`

### Hardware & Coding
- `board raspberry pi` / `board arduino` / `board esp32`
- `computer server` / `computer laptop`
- `architect robot humanoid`
- `architect machine factory line`
- `specific raspberry pi blink led`
- `specific arduino sensor read`

### System
- `run dir`
- `system`
- `exit` / `quit` / `goodbye`

## Technical Details

This version is optimized for VS Code and standard Python environments:

- **Speech and text interaction**: Speak commands naturally, with typed input as a fallback
- **Optional voice output**: Uses built-in Windows `System.Speech` or the Termux `termux-api` bridge when available
- **Speech recognition dependency**: Uses `SpeechRecognition` and `sounddevice` for microphone input
- **Cross-platform command base**: Core logic works on Windows, Linux, Termux, and other systems in text mode
- **Platform-aware app launching**: Uses Windows app launching, Linux `PATH`/`xdg-open`, or Android package launchers as appropriate
- **Context-aware**: Maintains conversation state for better responses

## Notes

- Spoken replies require Windows speech support or the Termux:API companion app; typed commands work without them
- Commands are case-insensitive
- Some commands (like `open`) look for installed applications by name
- Hardware board code generation provides framework templates for Raspberry Pi, Arduino, ESP32, Jetson, and PLC systems

## Inspiration

Designed with the conversational style and helpfulness of JARVIS from Iron Man in mind.
