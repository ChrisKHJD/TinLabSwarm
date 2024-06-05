import cv2
import json
import math
import requests
import numpy as np
import imutils
from inference import get_model

CAMERA_URL = "http://145.24.238.10:8080//shot.jpg"
MODEL_ID = "robot-location-and-orientation/1"
APIKEY = "CnyYmNzp3FktcouTB3d5"
FRAME_WIDTH = 960
FRAME_HEIGHT = 540

model = get_model(model_id=MODEL_ID, api_key=APIKEY)
chariots = {}

def calculate_angle(x1, y1, x2, y2):
    # Calculate the differences in coordinates
    delta_x = x1 - x2
    delta_y = y1 - y2

    # Calculate the angle using arctan2 and convert it to degrees
    angle_rad = math.atan2(delta_y, delta_x)
    angle_deg = math.degrees(angle_rad)

    # Ensure the angle is between 0 and 360 degrees
    mapped_angle = angle_deg % 360
    if mapped_angle < 0:
        mapped_angle += 360  # Ensure angle is positive

    return mapped_angle


def fetch_frame():
    try:
        img_resp = requests.get(CAMERA_URL)
        img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
        frame = cv2.imdecode(img_arr, -1)
        return imutils.resize(frame, width=FRAME_WIDTH, height=FRAME_HEIGHT)
    except Exception as e:
        print("Error fetching frame:", e)
        return None


def infer_frame(frame):
    try:
        response = model.infer(frame)
        json_data = json.dumps([ob.__dict__ for ob in response], default=lambda x: x.__dict__)
        data = json.loads(json_data)
        return data
    except Exception as e:
        print("Error during inference:", e)
        return None


def update_chariots(x, y, angle):
    global chariots
    if len(chariots) < 2:
        chariots[len(chariots)] = (x, y, angle)
    else:
        # om ervoor te zorgen dat robot 1, robot 1 blijft
        nearest_robot_id = None
        min_distance = float('inf')
        for robot_id, (robot_x, robot_y, _) in chariots.items():
            distance = math.sqrt((x - robot_x) ** 2 + (y - robot_y) ** 2)
            if distance < min_distance:
                min_distance = distance
                nearest_robot_id = robot_id
        chariots[nearest_robot_id] = (x, y, angle)


def process_inference(frame, data):
    if frame is None or data is None:
        print("no frame or no data")
        return None
    bottom_x, bottom_y = None, None
    top_x, top_y = None, None

    # er is altijd maar 1 element
    for element in data:
        count = 0
        # voor elke robot
        for prediction in element['predictions']:
            x = int(prediction['x'])
            y = int(prediction['y'])
            width = int(prediction['width'])
            height = int(prediction['height'])

            x1 = int(x - (width / 2))
            y1 = int(y - (height / 2))
            x2 = int(x + (width / 2))
            y2 = int(y + (height / 2))

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            for keypoint in prediction['keypoints']:
                keypoint_x = int(keypoint['x'])
                keypoint_y = int(keypoint['y'])
                class_name = keypoint['class_name']
                if class_name == 'top':
                    color = (0, 0, 255)
                    top_x, top_y = keypoint_x, keypoint_y
                elif class_name == 'bottom':
                    color = (255, 0, 0)
                    bottom_x, bottom_y = keypoint_x, keypoint_y
                else:
                    color = (0, 255, 0)
                cv2.circle(frame, (keypoint_x, keypoint_y), 5, color, -1)

            # Calculate the angle between top and bottom keypoints
            angle = calculate_angle(bottom_x, bottom_y, top_x, top_y)

            update_chariots(x, y, angle)

    return frame


# not used
def process_inference_noview(data):
    if data is None:
        print("no data")
        return None

    # Since there is always only one element in data
    for element in data:
        for prediction in element['predictions']:
            x = int(prediction['x'])
            y = int(prediction['y'])

            top_x, top_y, bottom_x, bottom_y = None, None, None, None

            for keypoint in prediction['keypoints']:
                keypoint_x = int(keypoint['x'])
                keypoint_y = int(keypoint['y'])
                class_name = keypoint['class_name']

                if class_name == 'top':
                    top_x, top_y = keypoint_x, keypoint_y
                elif class_name == 'bottom':
                    bottom_x, bottom_y = keypoint_x, keypoint_y

            if top_x is not None and top_y is not None and bottom_x is not None and bottom_y is not None:
                # Calculate the angle between top and bottom keypoints
                angle = calculate_angle(bottom_x, bottom_y, top_x, top_y)

                # Update chariots with the calculated angle
                update_chariots(x, y, angle)


def main():
    while True:
        frame = fetch_frame()
        data = infer_frame(frame)

        # for with view
        processed_frame = process_inference(frame, data)

        # for without view
        # processed_frame = None
        # process_inference_noview(data)

        print(chariots)
        if processed_frame is not None:
            cv2.imshow('Camera', processed_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
