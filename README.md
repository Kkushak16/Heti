# 🤖 Heti — AI Desktop Assistant & Handless Gesture Control System

**Heti** is an intelligent, modular AI desktop assistant for Windows. It features hands-free interaction through **webcam-based 3D hand gesture tracking** ("Handless Mode"), real-time **voice command automation**, local LLM integration (Ollama), and native system control tools.

---

## ✨ Key Features

* 🖐️ **Handless Mode (Camera Gesture Control):** Control your desktop cursor, mouse clicks, drag & drop, scrolling, and zooming using natural hand gestures captured by your webcam—100% locally with zero cloud streaming.
* 🎙️ **Voice AI Pipeline:** Speech-to-Text (STT) and Text-to-Speech (TTS) integration with passive wake-word standby ("Hey Heti"), a 2-stage active listening window, and zero intrusive repetitive audio loops.
* ⚡ **Fast-Path Intent Automation:** Sub-15ms execution for local OS actions (launching Chrome, Edge, Firefox, Explorer, direct website navigation, and system status queries).
* 🔔 **System Tray Integration:** Persistent background daemon (`pystray`) offering one-click toggles for Voice Listening and Handless Mode.
* 🌐 **WebSocket & Web App Bridge:** Real-time event broadcasting server (`ws://127.0.0.1:8765`) enabling web applications (such as [Ekam](https://github.com/Kkushak16/Ekam)) to render live gesture status and cursor telemetry.
* 🔒 **Privacy First:** All vision processing and voice inference are processed locally in RAM; webcam video feeds are never saved to disk or uploaded externally.

---

## 🖐️ Handless Mode Gesture Reference

Handless Mode relies on a 21-point MediaPipe hand landmark tracking engine with temporal debouncing, priority state resolution, and Exponential Moving Average (EMA) cursor smoothing:

| Gesture Pose | Hand Configuration | Action Executed |
| :--- | :--- | :--- |
| **Open Hand** | All 5 fingers extended | **Smooth Cursor Movement** (EMA Smoothed) |
| **Pinch In** | Thumb & Index tips moving closer | **Zoom In** (`Ctrl` + `+`) |
| **Pinch Out** | Thumb & Index tips moving apart | **Zoom Out** (`Ctrl` - `-`) |
| **Fist** | All fingers closed | **Drag & Drop** (Mouse Down $\rightarrow$ Drag $\rightarrow$ Mouse Up) |
| **Index Finger** | Index extended, others closed | **Right Click** |
| **Middle Finger** | Middle extended, others closed | **Left Click** |
| **Two Fingers** | Index + Middle extended, others closed | **Double Click** (or **Vertical Scroll** on vertical movement) |

---

## 📁 Repository Structure

```text
Heti/
├── agent/                # Core agent execution & fast-path intent matching
│   └── core_agent.py
├── config/               # Agent configuration settings & system constants
│   └── config_loader.py
├── gesture/              # Handless Mode gesture engine
│   ├── action_executor.py # PyAutoGUI OS action mapping layer
│   ├── classifier.py      # MediaPipe landmark gesture classifier
│   ├── config.py          # Centralized gesture configuration
│   ├── controller.py      # Singleton webcam capture & processing thread
│   ├── landmark_processor.py # 21-point 3D landmark normalization
│   ├── server.py          # Local WebSocket event broadcasting server
│   └── state_machine.py   # Debouncing & priority state machine
├── tools/                # Native OS automation tools
│   └── system_tools.py
├── voice/                # Speech-to-Text & Text-to-Speech pipeline
├── main.py               # Main CLI runtime script
├── tray_app.py           # Background system tray application
├── Start Heti.vbs        # Silent background launcher for Windows
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

* **Operating System:** Windows 10 / 11
* **Python:** Python 3.10+
* **Dependencies:** `opencv-python`, `mediapipe`, `pyautogui`, `pystray`, `websockets`, `pyttsx3`, `SpeechRecognition`

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Kkushak16/Heti.git
   cd Heti
   ```

2. Install Python dependencies:
   ```bash
   pip install opencv-python mediapipe pyautogui pystray websockets pyttsx3 SpeechRecognition
   ```

3. Launch Heti System Tray App:
   ```bash
   python tray_app.py
   ```

---

## 🎙️ Voice Commands

Once Heti is active, say **"Hey Heti"** followed by any of these commands:

* *"Enable handless mode"* / *"Turn on camera control"* — Starts webcam gesture tracking.
* *"Disable handless mode"* / *"Stop camera control"* — Stops tracking and releases webcam immediately.
* *"Check gesture status"* — Speaks and displays active gesture FPS and state.
* *"Open Google Chrome"* / *"Open File Explorer"* — Launches system applications directly.
* *"Open youtube.com"* / *"Go to github.com"* — Navigates directly to domains in default browser.

---

## 📜 Attributions & License

Licensed under the **Apache License 2.0**.

This project incorporates architectural patterns and gesture heuristics adapted from:
* [hand-gesture-recognition-mediapipe](https://github.com/kinivi/hand-gesture-recognition-mediapipe) by kinivi (Apache-2.0)
* [Hand-Gesture-Recognition-for-Cursor-Controlling](https://github.com/ahmed-0egy/Hand-Gesture-Recognition-for-Cursor-Controlling) by ahmed-0egy (Apache-2.0)
