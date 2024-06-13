import cv2
import json
import math
import requests
import numpy as np
import imutils
from inference import get_model
from time import sleep

CAMERA_URL = "http://145.24.243.14:8080//shot.jpg"
MODEL_ID = "robot-location-and-orientation/1"
APIKEY = "CnyYmNzp3FktcouTB3d5"
FRAME_WIDTH = 960
FRAME_HEIGHT = 540

model = get_model(model_id=MODEL_ID, api_key=APIKEY)
camera_chariots = {}
amount_robots_seen = 0
cap = None


def calculate_angle(front_x, front_y, back_x, back_y):
    dx = front_x - back_x
    dy = front_y - back_y
    return math.degrees(math.atan2(dy, dx))


def fetch_frame_phone():
    try:
        # print("1")
        img_resp = requests.get(CAMERA_URL)
        # print("2")
        img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
        # print("3")
        frame = cv2.imdecode(img_arr, -1)
        # print("4")
        return imutils.resize(frame, width=FRAME_WIDTH, height=FRAME_HEIGHT)
    except Exception as e:
        print("Error fetching frame:", e)
        return None


def fetch_frame_gopro():
    ret, frame = cap.read()
    frame = imutils.resize(frame, width=FRAME_WIDTH, height=FRAME_HEIGHT)
    return frame


def get_camera_and_set_capture():
    global cap
    index = 0
    available_cameras = []
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.read()[0]:
            break
        else:
            available_cameras.append(index)
        cap.release()
        index += 1
    cap = cv2.VideoCapture(available_cameras[1])


def infer_frame(frame):
    try:
        response = model.infer(frame)
        json_data = json.dumps(
            [ob.__dict__ for ob in response], default=lambda x: x.__dict__
        )
        data = json.loads(json_data)
        return data
    except Exception as e:
        print("Error during inference:", e)
        return None


#update this function so it takes a list of all robots that are detected, and if there are less robots detected than in the camera_chartios --> see wich one needs to be deleted by nearest neigbor
def update_chariots_old(x, y, angle):
    global camera_chariots, amount_robots_seen
    if len(camera_chariots) < amount_robots_seen:
        camera_chariots[len(camera_chariots)] = (x, y, angle)
    else:
        # om ervoor te zorgen dat robot 1, robot 1 blijft
        nearest_robot_id = None
        min_distance = float("inf")
        for robot_id, (robot_x, robot_y, _) in camera_chariots.items():
            distance = math.sqrt((x - robot_x) ** 2 + (y - robot_y) ** 2)
            if distance < min_distance:
                min_distance = distance
                nearest_robot_id = robot_id
        camera_chariots[nearest_robot_id] = (x, y, angle)


def update_chariots(robot_positions):
    global camera_chariots, amount_robots_seen
    if len(camera_chariots) != len(robot_positions):
        for robot_id, (robot_x, robot_y, _) in camera_chariots.items():
            (nearest_x, nearest_y, nearest_angle) = (0,0,0)
            min_distance = float("inf")
            #loop door de robot posities die binnen komen en kies de dichtbijzijnste
            for x, y, angle in robot_positions:
                distance = math.sqrt((x - robot_x) ** 2 + (y - robot_y) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    (nearest_x, nearest_y, nearest_angle) = (x, y, angle)
            camera_chariots[robot_id] = (nearest_x, nearest_y, nearest_angle)
            print(f"robot_positions: {robot_positions}, nearestX: {nearest_x}, nearestY: {nearest_y}, nearestAngle: {nearest_angle}")
            robot_positions.remove((nearest_x, nearest_y, nearest_angle))
        #add the remaining robots
        if len(camera_chariots) < len(robot_positions):
            for new_x, new_y, new_angle in robot_positions:
                camera_chariots[len(camera_chariots)] = (new_x, new_y, new_angle)
    else:
        for x, y, angle in robot_positions:
            nearest_robot_id = None
            min_distance = float("inf")
            for robot_id, (robot_x, robot_y, _) in camera_chariots.items():
                distance = math.sqrt((x - robot_x) ** 2 + (y - robot_y) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    nearest_robot_id = robot_id
            camera_chariots[nearest_robot_id] = (x, y, angle)

def process_inference_and_update_chariots(frame, data):
    global amount_robots_seen, camera_chariots
    if frame is None or data is None:
        print("no frame or no data")
        return None
    bottom_x, bottom_y = None, None
    top_x, top_y = None, None

    # er is altijd maar 1 element
    for element in data:
        update_chariots_list = []
        amount_robots_seen = len(element["predictions"])
        # if len(camera_chariots) > amount_robots_seen:
        #     camera_chariots = {} # slecht idee, want dan krijgen ze waarschijnlijk een ander id
        # voor elke robot
        for prediction in element["predictions"]:
            x = int(prediction["x"])
            y = int(prediction["y"])

            for keypoint in prediction["keypoints"]:
                keypoint_x = int(keypoint["x"])
                keypoint_y = int(keypoint["y"])
                class_name = keypoint["class_name"]
                if class_name == "top":
                    top_x, top_y = keypoint_x, keypoint_y
                elif class_name == "bottom":
                    bottom_x, bottom_y = keypoint_x, keypoint_y

            # Calculate the angle between top and bottom keypoints
            angle = calculate_angle(top_x, top_y, bottom_x, bottom_y)

            update_chariots_list.append((x, y, angle))
        update_chariots(update_chariots_list)

    return frame


def process_frame_and_return_chariots():
    frame = fetch_frame_phone()

    data = infer_frame(frame)

    processed_frame = process_inference_and_update_chariots(frame, data)
    # print(f"camera detected chariots: {camera_chariots}")

    return camera_chariots
