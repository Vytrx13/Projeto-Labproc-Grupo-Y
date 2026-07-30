import time
import socket
import cv2
import mediapipe as mp
import math

UDP_IP = "IP_DO_RASPBERRY_PI"
UDP_PORT = 5005

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
    return math.degrees(math.acos(cosine))

cap1 = cv2.VideoCapture(0)
cap2 = cv2.VideoCapture(1)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tip_ids = [4, 7, 11, 15, 19]
last_send_time = time.time()

while True:
    success1, img1 = cap1.read()
    success2, img2 = cap2.read()
    current_time = time.time()
    
    if (current_time - last_send_time) >= 0.5:
        if success1:
            img_rgb1 = cv2.cvtColor(cv2.flip(img1, 1), cv2.COLOR_BGR2RGB)
            results1 = hands.process(img_rgb1)
            if results1.multi_hand_landmarks:
                landmarks = results1.multi_hand_landmarks[0].landmark
                fingers1 = []
                dist = distance2D(landmarks[4], landmarks[9])
                fingers1.append(1 if dist > 0.15 else 0)
                for i in range(1, 5):
                    ang = angle(landmarks[tip_ids[i]], landmarks[tip_ids[i]-1], landmarks[tip_ids[i]-2])
                    fingers1.append(1 if 160 <= ang <= 180 else 0)
                msg1 = f"P1:{fingers1}"
                sock.sendto(msg1.encode('utf-8'), (UDP_IP, UDP_PORT))
                print(msg1)

        if success2:
            img_rgb2 = cv2.cvtColor(cv2.flip(img2, 1), cv2.COLOR_BGR2RGB)
            results2 = hands.process(img_rgb2)
            if results2.multi_hand_landmarks:
                landmarks = results2.multi_hand_landmarks[0].landmark
                fingers2 = []
                dist = distance2D(landmarks[4], landmarks[9])
                fingers2.append(1 if dist > 0.15 else 0)
                for i in range(1, 5):
                    ang = angle(landmarks[tip_ids[i]], landmarks[tip_ids[i]-1], landmarks[tip_ids[i]-2])
                    fingers2.append(1 if 160 <= ang <= 180 else 0)
                msg2 = f"P2:{fingers2}"
                sock.sendto(msg2.encode('utf-8'), (UDP_IP, UDP_PORT))
                print(msg2)

        last_send_time = current_time

    if success1:
        cv2.imshow("Camera P1", img1)
    if success2:
        cv2.imshow("Camera P2", img2)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap1.release()
cap2.release()
cv2.destroyAllWindows()