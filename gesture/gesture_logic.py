def detect_gesture(results):

    if not results.pose_landmarks:
        return "NONE"

    landmarks = results.pose_landmarks.landmark

    right_wrist = landmarks[16]
    right_shoulder = landmarks[12]

    left_wrist = landmarks[15]
    left_shoulder = landmarks[11]

    # Jump gesture
    if right_wrist.y < right_shoulder.y:
        return "JUMP"

    # Shoot gesture
    if left_wrist.y < left_shoulder.y:
        return "SHOOT"

    return "IDLE"