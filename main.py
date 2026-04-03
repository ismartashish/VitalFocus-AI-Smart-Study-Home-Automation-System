import cv2
import numpy as np
import time
import serial
import serial.tools.list_ports
from ultralytics import YOLO
import mediapipe as mp
from camera.camera_capture import start_camera
from pose.pose_detector import detect_pose

# =========================
# 🔌 SERIAL AUTO CONNECT
# =========================
def find_esp32_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if any(k in port.description.lower() for k in ["cp210", "ch340", "usb"]):
            return port.device
    return None

port = find_esp32_port() or "COM7"
try:
    ser = serial.Serial(port, 115200, timeout=1)
    time.sleep(2)
    print("ESP32 Connected:", port)
except:
    ser = None
    print("ESP32 NOT Connected")

# =========================
# 🤖 YOLO MODEL
# =========================
model = YOLO("yolov8n.pt")

# =========================
# ✋ MEDIAPIPE HANDS
# =========================
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands_det = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.75,
    min_tracking_confidence=0.6
)

# =========================
# 📐 HELPERS
# =========================
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return int(360 - angle if angle > 180 else angle)

def smooth(prev, new):
    return int(0.8 * prev + 0.2 * new)

# =========================
# 🏠 HOME STATE
# =========================
home_state = {
    "light": False,
    "fan": False,
    "ac": False,
    "fan_speed": 1,
    "ac_temp": 24,
}

# =========================
# 🎛️ VIRTUAL BUTTONS
# =========================
BUTTONS = [
    {"label": "LIGHT",   "key": "light",     "type": "toggle", "row": 0, "col": 0},
    {"label": "FAN",     "key": "fan",       "type": "toggle", "row": 1, "col": 0},
    {"label": "AC",      "key": "ac",        "type": "toggle", "row": 2, "col": 0},
    {"label": "ALL ON",  "key": "all_on",    "type": "special", "row": 3, "col": 0},
    {"label": "ALL OFF", "key": "all_off",   "type": "special", "row": 3, "col": 1},
]

N = len(BUTTONS)
hover_start = [0.0] * N
hover_fired = [False] * N
HOVER_SECS = 1.0
last_action = ""
last_action_timer = 0.0

# =========================
# STUDY GLOBALS + 10 SEC DISTRACTION TIMER
# =========================
prev_r = prev_l = 90
movement_history = []
focus_buffer = []
focus_time = 0
distraction_time = 0
break_time = 0

distraction_start_time = 0.0      # When distraction started
DISTRACTION_DELAY = 10.0          # 10 seconds continuous distraction

HEAD_MIN = 80
HEAD_MAX = 100
MOVEMENT_THRESHOLD = 15
BUFFER_SIZE = 15
FOCUS_SCORE = 10

# =========================
# STUDY FUNCTIONS
# =========================
def is_head_focused(h): 
    return HEAD_MIN <= h <= HEAD_MAX

def is_stable(r, l):
    global movement_history, prev_r, prev_l
    m = abs(r - prev_r) + abs(l - prev_l)
    movement_history.append(m)
    if len(movement_history) > 10: 
        movement_history.pop(0)
    avg = sum(movement_history) / len(movement_history)
    return avg < MOVEMENT_THRESHOLD, avg

def get_focus_status(head, r, l):
    global focus_buffer
    ok = is_head_focused(head) and is_stable(r, l)[0]
    focus_buffer.append(1 if ok else 0)
    if len(focus_buffer) > BUFFER_SIZE: 
        focus_buffer.pop(0)
    return "FOCUSED" if sum(focus_buffer) > FOCUS_SCORE else "DISTRACTED"

def detect_objects(frame):
    res = model(frame, verbose=False)
    objs = []
    for r in res:
        for box in r.boxes:
            cls = int(box.cls[0])
            lbl = model.names[cls]
            objs.append(lbl)
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.putText(frame, lbl, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    return objs

def detect_behavior(objs, head):
    if "book" in objs:
        return "FOCUSED"                    # Book = No distraction

    if "cell phone" in objs or objs.count("person") > 1:
        return "DISTRACTED"
    if head < 70:
        return "BREAK"
    return None

# =========================
# 🔥 FIRE BUTTON ACTION
# =========================
def fire_button(i):
    global last_action, last_action_timer
    b = BUTTONS[i]
    t = b["type"]
    k = b["key"]

    if t == "toggle":
        home_state[k] = not home_state[k]
        last_action = f"{b['label']} {'ON' if home_state[k] else 'OFF'}"
    elif t == "special":
        v = (k == "all_on")
        home_state["light"] = home_state["fan"] = home_state["ac"] = v
        last_action = "ALL ON" if v else "ALL OFF"

    last_action_timer = time.time()
    print(f"[HOME] {last_action}")

# =========================
# 📡 SEND TO ESP32
# =========================
def send_data(status, buzzer_on):
    if ser:
        try:
            # Send STUDY status with buzzer state
            ser.write(f"STUDY,{status},{focus_time},{distraction_time},{break_time},{1 if buzzer_on else 0}\n".encode())
            ser.write((
                f"HOME,"
                f"{1 if home_state['light'] else 0},"
                f"{1 if home_state['fan'] else 0},"
                f"{home_state['fan_speed']},"
                f"{1 if home_state['ac'] else 0},"
                f"{home_state['ac_temp']}\n"
            ).encode())
        except:
            pass

# =========================
# 🎨 COMPUTE BUTTON RECTS
# =========================
def compute_rects(W, H):
    PANEL_W = 200
    PX = W - PANEL_W - 20
    PY = 60
    ROW_H = 62
    PAD = 8
    TOG_W = 135
    BTN_H = 46

    rects = []
    for b in BUTTONS:
        r = b["row"]
        c = b["col"]
        y1 = PY + r * ROW_H + PAD
        y2 = y1 + BTN_H

        if b["type"] == "special":
            half = (PANEL_W - PAD * 3) // 2
            x1 = PX + PAD + c * (half + PAD)
            x2 = x1 + half
        else:
            x1 = PX + PAD
            x2 = x1 + TOG_W

        rects.append((x1, y1, x2, y2))
    return rects, PX, PY, PANEL_W

# =========================
# 🖥️ DRAW PANEL
# =========================
def draw_panel(frame, rects, PX, PY, PANEL_W, cursor):
    H, W = frame.shape[:2]
    now = time.time()

    rows = 4
    panel_h = rows * 62 + 30
    ov = frame.copy()
    cv2.rectangle(ov, (PX, PY - 25), (W - 10, PY + panel_h), (20, 20, 25), -1)
    cv2.addWeighted(ov, 0.82, frame, 0.18, 0, frame)
    cv2.rectangle(frame, (PX, PY - 25), (W - 10, PY + panel_h), (70, 70, 100), 2)

    cv2.putText(frame, "SMART HOME CONTROL", (PX + 12, PY - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (140, 180, 255), 2)

    cv2.putText(frame, f"Fan Speed : {home_state['fan_speed']}", 
                (PX + 15, PY + 62*1 + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1)
    cv2.putText(frame, f"AC Temp   : {home_state['ac_temp']}°C", 
                (PX + 15, PY + 62*2 + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1)

    for i, (b, rect) in enumerate(zip(BUTTONS, rects)):
        x1, y1, x2, y2 = rect
        mx = (x1 + x2) // 2
        my = (y1 + y2) // 2
        t = b["type"]
        k = b["key"]

        inside = (cursor is not None and x1 <= cursor[0] <= x2 and y1 <= cursor[1] <= y2)

        if inside:
            if hover_start[i] == 0.0:
                hover_start[i] = now
            elapsed = now - hover_start[i]
            progress = min(elapsed / HOVER_SECS, 1.0)
            if progress >= 1.0 and not hover_fired[i]:
                hover_fired[i] = True
                fire_button(i)
        else:
            hover_start[i] = 0.0
            hover_fired[i] = False
            progress = 0.0

        if t == "toggle":
            on = home_state[k]
            bg = (0, 160, 80) if on else (45, 45, 55)
            border = (0, 255, 140) if on else (90, 90, 110)
            txt_col = (255, 255, 255)
        else:
            on = (k == "all_on")
            bg = (0, 120, 200) if on else (160, 40, 40)
            border = (100, 210, 255) if on else (255, 90, 90)
            txt_col = (255, 255, 255)

        if inside:
            bg = tuple(min(255, c + 40) for c in bg)
            border = (0, 240, 255)

        cv2.rectangle(frame, (x1, y1), (x2, y2), bg, -1)
        cv2.rectangle(frame, (x1+1, y1+1), (x2-1, y1+6), tuple(min(255, c+55) for c in bg), -1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), border, 2)

        if progress > 0:
            fill = int((x2 - x1) * progress)
            cv2.rectangle(frame, (x1, y2-6), (x1 + fill, y2), (0, 230, 255), -1)

        fs = 0.58
        (tw, th), _ = cv2.getTextSize(b["label"], cv2.FONT_HERSHEY_SIMPLEX, fs, 2)
        cv2.putText(frame, b["label"], (mx - tw//2, my + th//2),
                    cv2.FONT_HERSHEY_SIMPLEX, fs, txt_col, 2)

        if t == "toggle":
            on = home_state[k]
            dot_col = (0, 255, 110) if on else (80, 80, 80)
            cv2.circle(frame, (x2 - 14, y1 + 12), 5, dot_col, -1)

    # Action banner
    elapsed_action = now - last_action_timer
    if last_action and elapsed_action < 2.2:
        alpha = max(0.0, 1.0 - elapsed_action / 2.2)
        ov2 = frame.copy()
        mid = H // 2
        cv2.rectangle(ov2, (0, mid-30), (W, mid+30), (0, 0, 0), -1)
        cv2.addWeighted(ov2, alpha*0.65, frame, 1-alpha*0.65, 0, frame)
        (tw, th), _ = cv2.getTextSize(last_action, cv2.FONT_HERSHEY_SIMPLEX, 1.35, 3)
        cv2.putText(frame, last_action, (W//2 - tw//2, mid + th//2 + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.35, (0, 255, 220), 3)

# =========================
# 📷 MAIN LOOP
# =========================
cap = start_camera()
cv2.namedWindow("Smart Study + Home AI", cv2.WINDOW_NORMAL)

while True:
    ret, frame = cap.read()
    if not ret: 
        break

    frame = cv2.flip(frame, 1)
    H, W = frame.shape[:2]
    now = time.time()

    rects, PX, PY, PW = compute_rects(W, H)

    objects = detect_objects(frame)
    frame, results = detect_pose(frame)

    study_status = "UNKNOWN"
    buzzer_should_play = False

    if results.pose_landmarks:
        lm = results.pose_landmarks.landmark
        r_sh = [lm[12].x, lm[12].y]; r_el = [lm[14].x, lm[14].y]; r_wr = [lm[16].x, lm[16].y]
        l_sh = [lm[11].x, lm[11].y]; l_el = [lm[13].x, lm[13].y]; l_wr = [lm[15].x, lm[15].y]

        rea = smooth(prev_r, calculate_angle(r_sh, r_el, r_wr))
        lea = smooth(prev_l, calculate_angle(l_sh, l_el, l_wr))
        hd = int(90 + (lm[0].x - (lm[2].x + lm[5].x)/2) * 300)

        sp = detect_behavior(objects, hd)
        study_status = sp if sp else get_focus_status(hd, rea, lea)

        # ==================== 10 SECOND DISTRACTION LOGIC ====================
        if study_status == "DISTRACTED":
            if distraction_start_time == 0.0:
                distraction_start_time = now
            
            elapsed_distraction = now - distraction_start_time
            
            if elapsed_distraction >= DISTRACTION_DELAY:
                buzzer_should_play = True
        else:
            distraction_start_time = 0.0   # Reset timer when not distracted

        # Time counting
        if study_status == "FOCUSED":
            focus_time += 1
        elif study_status == "DISTRACTED":
            distraction_time += 1
        else:
            break_time += 1

        prev_r, prev_l = rea, lea

        col = (0, 255, 0) if study_status == "FOCUSED" else (0, 100, 255)
        cv2.putText(frame, study_status, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.1, col, 3)
        
        # Show distraction timer
        if study_status == "DISTRACTED" and distraction_start_time > 0:
            remaining = DISTRACTION_DELAY - (now - distraction_start_time)
            if remaining > 0:
                cv2.putText(frame, f"Distraction: {remaining:.1f}s", 
                            (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 165, 255), 2)
            else:
                cv2.putText(frame, "BUZZER ACTIVE", (20, 120), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Hand Detection
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hand_res = hands_det.process(rgb)
    cursor = None
    if hand_res.multi_hand_landmarks:
        for hlm in hand_res.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hlm, mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=(80,220,255), thickness=2, circle_radius=3),
                mp_draw.DrawingSpec(color=(40,140,255), thickness=2))
            tip = hlm.landmark[8]
            cursor = (int(tip.x * W), int(tip.y * H))
        if cursor:
            cv2.circle(frame, cursor, 18, (0, 255, 255), 3)
            cv2.circle(frame, cursor, 5, (0, 255, 255), -1)

    draw_panel(frame, rects, PX, PY, PW, cursor)

    cv2.putText(frame, "Book = No distraction | 10 sec continuous distraction → Buzzer ON", 
                (20, H - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (110, 110, 130), 1)

    # Send data to ESP32 with buzzer status
    send_data(study_status, buzzer_should_play)

    cv2.imshow("Smart Study + Home AI", frame)
    
    if cv2.waitKey(1) == 27: 
        break

cap.release()
cv2.destroyAllWindows()