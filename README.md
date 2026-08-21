# 🤖 Heti — AI Desktop Assistant & Handless Gesture Control System

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![MediaPipe Tracking](https://img.shields.io/badge/MediaPipe-21_Hand_Landmarks-green.svg)](https://google.github.io/mediapipe/)
[![OpenCV Powered](https://img.shields.io/badge/OpenCV-Computer_Vision-orange.svg)](https://opencv.org/)
[![License Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Platform Windows](https://img.shields.io/badge/platform-Windows_10%2F11-0078D6.svg)](https://microsoft.com/windows)

**Heti** is a privacy-first, high-performance AI desktop assistant and hands-free computer vision controller for Windows. It features **webcam 3D hand landmark gesture tracking** ("Handless Mode"), real-time **voice command automation**, local LLM execution via Ollama, and instant OS automation.

> **SEO Keywords:** `hand gesture control`, `mediapipe cursor control`, `voice AI assistant python`, `handless mode computer vision`, `desktop gesture navigation`, `local AI assistant`.

---

## 📑 Table of Contents
- [✨ Key Features](#-key-features)
- [🖐️ Handless Mode Gesture Reference](#️-handless-mode-gesture-reference)
- [📁 Repository Structure](#-repository-structure)
- [🚀 Getting Started](#-getting-started)
- [🎙️ Voice Commands](#️-voice-commands)
- [🔒 Privacy & Security Audit](#-privacy--security-audit)
- [📜 Attributions & License](#-attributions--license)

---

## ✨ Key Features

* 🖐️ **Handless Mode (Webcam Gesture Control):** Control your desktop cursor, mouse clicks, drag & drop, scrolling, and zooming using natural hand gestures captured by your webcam—100% locally in RAM with zero cloud video streaming.
* 🎙️ **Voice AI Pipeline:** Speech-to-Text (STT) and Text-to-Speech (TTS) integration with passive wake-word standby ("Hey Heti"), a 2-stage active listening window, and zero intrusive audio feedback loops.
* ⚡ **Fast-Path Intent Automation:** Sub-15ms execution for local OS actions (launching Chrome, Edge, Firefox, Explorer, direct website navigation, and system status queries).
* 🔔 **System Tray Integration:** Persistent background daemon (`pystray`) offering one-click toggles for Voice Listening and Handless Mode.
* 🌐 **WebSocket & Web App Bridge:** Real-time event broadcasting server (`ws://127.0.0.1:8765`) enabling web applications (such as [Ekam](https://github.com/Kkushak16/Ekam)) to render live gesture telemetry and status indicators.
* 🔒 **Zero Data Leakage:** Video frames and voice inputs stay 100% on-device. No telemetry or secret tokens are stored or sent across external networks.

---

## 🖐️ Handless Mode Gesture Reference

Handless Mode relies on a 21-point MediaPipe hand landmark tracking engine with temporal candidate debouncing, priority state resolution, and Exponential Moving Average (EMA) cursor smoothing:

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

## 🔒 Privacy & Security Audit

- **Zero Credential Storage:** `.gitignore` strictly blocks `.env`, keys, credentials, tokens, and database files.
- **Local In-Memory Video:** Frames are processed frame-by-frame in RAM and released immediately.
- **No Remote Telemetry:** All communication stays on local loopback interface (`127.0.0.1`).

---

## 📜 Attributions & License

Licensed under the **Apache License 2.0**.

This project incorporates architectural patterns and gesture heuristics adapted from:
* [hand-gesture-recognition-mediapipe](https://github.com/kinivi/hand-gesture-recognition-mediapipe) by kinivi (Apache-2.0)
* [Hand-Gesture-Recognition-for-Cursor-Controlling](https://github.com/ahmed-0egy/Hand-Gesture-Recognition-for-Cursor-Controlling) by ahmed-0egy (Apache-2.0)
