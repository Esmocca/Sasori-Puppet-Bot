#!/usr/bin/env python3

import cv2
import numpy as np
import serial
import rospy
import time
import os
import threading
import subprocess
import time

from std_msgs.msg import String

# =========================
# CONFIG
# =========================

CAMERA_DEVICE = "/dev/video0"
SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 115200

INIT_YAW = 90
INIT_PITCH = 0 #semakinkecil semakin keatas
INIT_MOUTH = 0

YAW_MIN = 0
YAW_MAX = 140

PITCH_MIN = 10
PITCH_MAX = 80

DEADZONE_X = 25
DEADZONE_Y = 10

SEARCH_TIMEOUT = 30

SEARCH_YAW_STEP = 2
SEARCH_PITCH_STEP = 5

# =========================
# ROS
# =========================

rospy.init_node("hand_tracking_node")

pub = rospy.Publisher(
    "/head_tracking",
    String,
    queue_size=10
)

# =========================
# SERIAL
# =========================

ser = None

def connect_serial():

    global ser

    while not rospy.is_shutdown():

        try:

            ser = serial.Serial(
                SERIAL_PORT,
                BAUDRATE,
                timeout=1
            )

            time.sleep(2)

            print("Serial connected")

            return

        except Exception as e:

            print(f"Serial error: {e}")

            time.sleep(2)

def reconnect_serial():

    global ser

    try:
        ser.close()
    except:
        pass

    connect_serial()

connect_serial()

# =========================
# CAMERA
# =========================

def open_camera():

    while not rospy.is_shutdown():

        if not os.path.exists(CAMERA_DEVICE):

            print(f"{CAMERA_DEVICE} tidak ditemukan")

            time.sleep(2)

            continue

        print(f"Mencoba membuka {CAMERA_DEVICE} ...")

        cap = cv2.VideoCapture(CAMERA_DEVICE)

        if cap.isOpened():

            print(f"{CAMERA_DEVICE} berhasil dibuka")

            cap.set(
                cv2.CAP_PROP_FRAME_WIDTH,
                1280
            )

            cap.set(
                cv2.CAP_PROP_FRAME_HEIGHT,
                720
            )

            return cap

        print(f"Gagal membuka {CAMERA_DEVICE}")

        time.sleep(2)

# =========================
# OPEN CAMERA
# =========================

cap = open_camera()

# =========================
# INIT SERVO
# =========================

yaw = INIT_YAW
pitch = INIT_PITCH
mouth = INIT_MOUTH

smooth_yaw = INIT_YAW
smooth_pitch = INIT_PITCH

search_yaw_dir = 1
search_pitch_dir = 1

lost_counter = 0

current_mode = "TRACKING"

def get_battery_percent():

    try:

        with open(
            "/sys/class/power_supply/BAT0/capacity"
        ) as f:

            return int(f.read().strip())

    except:

        return 100
def get_battery_status():

    try:

        with open(
            "/sys/class/power_supply/BAT0/status"
        ) as f:

            return f.read().strip()

    except:

        return "Unknown"
    
last_low_bat = 0
full_notified = False

def battery_monitor():

    global last_low_bat
    global full_notified

    while not rospy.is_shutdown():

        battery = get_battery_percent()
        status = get_battery_status()

        # LOW BATTERY
        if battery < 20 and status != "Charging":

            now = time.time()

            if now - last_low_bat > 30:

                ser.write(b"LOW_BAT\n")

                last_low_bat = now

        # FULL BATTERY
        if battery >= 100:

            if not full_notified:

                ser.write(b"FULL_BAT\n")
                print("SEND FULL_BAT")

                full_notified = True

        else:

            full_notified = False

        time.sleep(5)

threading.Thread(
    target=battery_monitor,
    daemon=True
).start()

# =========================
# SEND INIT POSE
# =========================

init_data = f"{INIT_YAW},{INIT_PITCH},{INIT_MOUTH}\n"

for _ in range(10):

    try:

        ser.write(
            init_data.encode()
        )

        pub.publish(
            init_data
        )

    except:
        pass

    time.sleep(0.1)

time.sleep(2)

print(
    f"INIT POSE -> "
    f"Yaw:{INIT_YAW} "
    f"Pitch:{INIT_PITCH}"
)

# =========================
# MAIN LOOP
# =========================

while not rospy.is_shutdown():

    ret, frame = cap.read()

    # =====================
    # CAMERA RECONNECT
    # =====================

    if not ret:

        print("Frame gagal dibaca")

        try:
            cap.release()
        except:
            pass

        print(
            f"Reconnect {CAMERA_DEVICE}"
        )

        time.sleep(1)

        cap = open_camera()

        continue

    # =====================
    # MIRROR
    # =====================

    frame = cv2.flip(
        frame,
        1
    )

    frame_height, frame_width, _ = frame.shape

    center_screen_x = frame_width // 2
    center_screen_y = frame_height // 2

    # =====================
    # HSV
    # =====================

    hsv = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2HSV
    )

    lower_skin = np.array(
        [0,15,40],
        dtype=np.uint8
    )

    upper_skin = np.array(
        [25,255,255],
        dtype=np.uint8
    )

    mask = cv2.inRange(
        hsv,
        lower_skin,
        upper_skin
    )

    kernel = np.ones(
        (7,7),
        np.uint8
    )

    mask = cv2.erode(
        mask,
        kernel,
        iterations=4
    )

    mask = cv2.dilate(
        mask,
        kernel,
        iterations=1
    )

    mask = cv2.GaussianBlur(
        mask,
        (7,7),
        0
    )

    # =====================
    # CONTOUR
    # =====================

    contours_info = cv2.findContours(
        mask,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if len(contours_info) == 3:

        _, contours, _ = contours_info

    else:

        contours, _ = contours_info

    mouth = 0

    # =====================
    # TRACKING
    # =====================

    if contours:

        cnt = max(
            contours,
            key=cv2.contourArea
        )

        area = cv2.contourArea(
            cnt
        )

        if area > 2000:

            lost_counter = 0

            current_mode = "TRACKING"

            mouth = 30

            x,y,w,h = cv2.boundingRect(
                cnt
            )

            hand_x = x + w//2
            hand_y = y + h//2

            cv2.rectangle(
                frame,
                (x,y),
                (x+w,y+h),
                (0,255,0),
                2
            )

            cv2.circle(
                frame,
                (hand_x,hand_y),
                8,
                (0,0,255),
                -1
            )

            dx = (
                hand_x -
                center_screen_x
            )

            dy = (
                hand_y -
                center_screen_y
            )

            if abs(dx) > DEADZONE_X:

                yaw = int(
                    (
                        hand_x /
                        frame_width
                    ) * 180
                )

            if abs(dy) > DEADZONE_Y:

                pitch = int(
                    PITCH_MIN +
                    (
                        hand_y /
                        frame_height
                    ) *
                    (
                        PITCH_MAX -
                        PITCH_MIN
                    )
                )

            yaw = max(
                YAW_MIN,
                min(
                    YAW_MAX,
                    yaw
                )
            )

            pitch = max(
                PITCH_MIN,
                min(
                    PITCH_MAX,
                    pitch
                )
            )

            smooth_yaw = int(
                smooth_yaw +
                (
                    yaw -
                    smooth_yaw
                ) * 0.15
            )

            smooth_pitch = int(
                smooth_pitch +
                (
                    pitch -
                    smooth_pitch
                ) * 0.15
            )

        else:

            lost_counter += 1

    else:

        lost_counter += 1

    # =====================
    # SEARCH MODE
    # =====================

    if lost_counter > SEARCH_TIMEOUT:

        current_mode = "SEARCHING"

        mouth = 0

        yaw += (
            SEARCH_YAW_STEP *
            search_yaw_dir
        )

        if yaw >= YAW_MAX:

            yaw = YAW_MAX

            search_yaw_dir = -1

            pitch += (
                SEARCH_PITCH_STEP *
                search_pitch_dir
            )

        elif yaw <= YAW_MIN:

            yaw = YAW_MIN

            search_yaw_dir = 1

            pitch += (
                SEARCH_PITCH_STEP *
                search_pitch_dir
            )

        if pitch >= PITCH_MAX:

            pitch = PITCH_MAX

            search_pitch_dir = -1

        elif pitch <= PITCH_MIN:

            pitch = PITCH_MIN

            search_pitch_dir = 1

        smooth_yaw = int(
            smooth_yaw +
            (
                yaw -
                smooth_yaw
            ) * 0.15
        )

        smooth_pitch = int(
            smooth_pitch +
            (
                pitch -
                smooth_pitch
            ) * 0.15
        )

    # =====================
    # SERIAL DATA
    # =====================

    serial_data = (
        f"{smooth_yaw},"
        f"{smooth_pitch},"
        f"{mouth}\n"
    )

    print(serial_data.strip())

    try:

        ser.write(
            serial_data.encode()
        )

    except:

        print(
            "Serial disconnect"
        )

        reconnect_serial()

    pub.publish(
        serial_data
    )

    # =====================
    # DISPLAY
    # =====================

    cv2.putText(
        frame,
        f"MODE: {current_mode}",
        (10,30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0,255,255),
        2
    )

    cv2.putText(
        frame,
        f"Yaw: {smooth_yaw}",
        (10,70),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255,0,0),
        2
    )

    cv2.putText(
        frame,
        f"Pitch: {smooth_pitch}",
        (10,110),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255,0,0),
        2
    )

    cv2.line(
        frame,
        (
            center_screen_x-20,
            center_screen_y
        ),
        (
            center_screen_x+20,
            center_screen_y
        ),
        (255,255,255),
        2
    )

    cv2.line(
        frame,
        (
            center_screen_x,
            center_screen_y-20
        ),
        (
            center_screen_x,
            center_screen_y+20
        ),
        (255,255,255),
        2
    )

    # cv2.imshow(
    #     "Hand Tracking",
    #     frame
    # )

    # cv2.imshow(
    #     "Mask",
    #     mask
    # )

    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break

# =========================
# CLEANUP
# =========================

try:
    cap.release()
except:
    pass
try: 
    cv2.destroyAllWindows()
except:
    pass

try:
    ser.close()
except:
    pass
