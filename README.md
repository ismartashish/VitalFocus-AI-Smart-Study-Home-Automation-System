# 🧠 VitalFocus AI — Smart Study & Home Automation System

> **An AI-powered real-time system that monitors student focus using computer vision and controls smart home appliances — all through a single camera feed.**

---

## 📌 Project Bio

**VitalFocus AI** is an intelligent desktop application built with Python that combines **pose estimation**, **object detection**, **hand gesture control**, and **IoT communication** into one unified pipeline.

It watches you study through your webcam — detecting whether you're focused, distracted, or taking a break — and simultaneously lets you control smart home devices (light, fan, AC) using just your hand gestures hovering over virtual buttons on screen.

When distraction is detected continuously for **10 seconds**, the system automatically triggers a **buzzer alert** via an ESP32 microcontroller over serial communication. The home appliance states (light, fan, fan speed, AC, AC temperature) are also synced to the ESP32 in real time.

This project is ideal as a **student productivity tool**, **smart home demo**, or an **IoT + AI portfolio project**.

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 🎯 Focus Detection | Detects FOCUSED / DISTRACTED / BREAK states using pose landmarks |
| 📦 Object Detection | YOLOv8 detects books, phones, multiple persons |
| ✋ Hand Gesture Control | Index finger hover activates virtual smart home buttons |
| 🏠 Smart Home Panel | Toggle Light, Fan, AC — All ON / ALL OFF |
| ⏱️ Distraction Timer | 10-second continuous distraction triggers buzzer |
| 📡 ESP32 Serial Sync | Sends study status + home state to ESP32 over COM7 |
| 🔔 Buzzer Alert | Auto-alert after sustained distraction |

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **OpenCV** — Camera capture & UI rendering
- **MediaPipe** — Pose estimation + hand landmark detection
- **Ultralytics YOLOv8** — Real-time object detection
- **PySerial** — ESP32 serial communication
- **NumPy** — Angle calculations & smoothing
- **ESP32** — Microcontroller for home control & buzzer

---

## 📁 Project Structure

```
VitalFocus-AI/
│
├── main.py                  # Main application entry point
├── camera/
│   └── camera_capture.py    # Camera initialization
├── pose/
│   └── pose_detector.py     # MediaPipe pose detection wrapper
├── yolov8n.pt               # YOLOv8 nano model weights
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourname/vitalfocus-ai.git
cd vitalfocus-ai
```

### 2. Install dependencies
```bash
pip install opencv-python mediapipe ultralytics pyserial numpy
```

### 3. Download YOLOv8 model
```bash
# Automatically downloaded on first run, or manually:
pip install ultralytics
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### 4. Connect ESP32
- Connect ESP32 via USB
- Update port in `main.py` if needed (default: `COM7`)
- Baud rate: `115200`

---

## 🚀 Running the App

```bash
python main.py
```

- Press **ESC** to exit
- Place your **index finger tip** over a button and hold for **1 second** to activate it
- Sit in front of the camera for focus detection to work

---

## 📡 ESP32 Serial Protocol

The system sends two types of serial messages every frame:

```
STUDY,FOCUSED,120,30,10,0        # status, focus_time, distraction_time, break_time, buzzer
HOME,1,1,2,0,24                  # light, fan, fan_speed, ac, ac_temp
```

---

## 🎯 Focus Detection Logic

| Condition | Status |
|-----------|--------|
| Head angle 80–100° + stable arms | FOCUSED |
| Book detected by YOLO | FOCUSED |
| Phone detected / multiple persons | DISTRACTED |
| Head angle < 70° | BREAK |
| Distracted > 10 seconds | BUZZER ON |

---

## 🏠 Smart Home Buttons

| Button | Action |
|--------|--------|
| LIGHT | Toggle light ON/OFF |
| FAN | Toggle fan ON/OFF |
| AC | Toggle AC ON/OFF |
| ALL ON | Turn all appliances ON |
| ALL OFF | Turn all appliances OFF |

---

## ⚠️ Alert System

- Distraction timer starts counting when DISTRACTED state is detected
- If distraction is **continuous for 10 seconds** → `buzzer_should_play = True`
- Buzzer state is sent to ESP32 via serial
- Timer **resets** as soon as focus is regained

---

## 🔧 Configuration

You can tweak these constants in `main.py`:

```python
HOVER_SECS        = 1.0   # Seconds to hover to activate button
DISTRACTION_DELAY = 10.0  # Seconds before buzzer triggers
HEAD_MIN          = 80    # Min head angle for focus
HEAD_MAX          = 100   # Max head angle for focus
MOVEMENT_THRESHOLD = 15   # Max arm movement for "stable"
BUFFER_SIZE       = 15    # Smoothing buffer size
FOCUS_SCORE       = 10    # Min focus frames in buffer
```

---

## 📸 How It Works

```
Camera Feed
    │
    ├── YOLOv8 Object Detection  →  Book / Phone / Person
    │
    ├── MediaPipe Pose           →  Head angle + Arm angles
    │       │
    │       └── Focus Status:  FOCUSED / DISTRACTED / BREAK
    │
    ├── MediaPipe Hands          →  Index finger cursor
    │       │
    │       └── Virtual Button Hover  →  Smart Home Control
    │
    └── Serial Output  →  ESP32  →  Relay / Buzzer / Display
```

---

## 📋 Requirements

```
opencv-python
mediapipe
ultralytics
pyserial
numpy
```

---

## 🙌 Credits

Built using open-source AI tools — MediaPipe, YOLOv8, OpenCV.

---

## 📄 License

MIT License — free to use, modify, and distribute.
