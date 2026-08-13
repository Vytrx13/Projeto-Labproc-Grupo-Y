import time
import socket
import cv2
import mediapipe as mp
import socket
import math

UDP_IP = "10.31.191.165"
UDP_PORT=5006


def distance2D(a, b):
    coords = (a.x - b.x, a.y - b.y)
    return math.sqrt(coords[0]**2 + coords[1]**2)

def angle(a, b, c):

    ab = (a.x - b.x, a.y - b.y, a.z - b.z)
    cb = (c.x - b.x, c.y - b.y, c.z - b.z)

    dot = ab[0]*cb[0] + ab[1]*cb[1] + ab[2]*cb[2]

    mod_ab = math.sqrt(ab[0]**2 + ab[1]**2 + ab[2]**2)
    mod_cb = math.sqrt(cb[0]**2 + cb[1]**2 + cb[2]**2)

    cosine = dot / (mod_ab * mod_cb)

    angle = math.degrees(math.acos(cosine))

    return angle


cap = cv2.VideoCapture(1)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

tip_ids = [4, 7, 11, 15, 19]
prev_time = 0

while True:
    success, img = cap.read()
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time

    if not success:
        break

    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    total_fingers = 0

    if results.multi_hand_landmarks:

        for hand_landmarks in results.multi_hand_landmarks:

            landmarks = hand_landmarks.landmark

            fingers = []            
            dist = distance2D(landmarks[4], landmarks[9])
            if 0.15 < dist:
                fingers.append(1)
            else:
                fingers.append(0)

            for i in range(1, 5):
                ang = angle(landmarks[tip_ids[i]], landmarks[tip_ids[i]-1], landmarks[tip_ids[i]-2])
                if 160 <= ang <= 180 :
                    fingers.append(1)
                else:
                    fingers.append(0)

            total_fingers = sum(fingers)
            MESSAGE= fingers
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(str(MESSAGE).encode('utf-8'), (UDP_IP, UDP_PORT))
            print(fingers)

            mp_draw.draw_landmarks(
                img,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    cv2.putText(
        img,
        f'Dedos: {total_fingers}',
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (0, 255, 0),
        3
    )


    cv2.imshow("Finger Counter", img)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()