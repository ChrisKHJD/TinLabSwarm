import cv2
import json
import math
import requests
import numpy as np
import imutils
from inference import get_model
from time import sleep

CAMERA_URL = "http://145.24.243.11:8080//shot.jpg"
MODEL_ID = "robot-location-and-orientation/1"
APIKEY = "CnyYmNzp3FktcouTB3d5"
FRAME_WIDTH = 960
FRAME_HEIGHT = 540

model = get_model(model_id=MODEL_ID, api_key=APIKEY)
camera_chariots = {}
amount_robots_seen = 0


def calculate_angle(front_x, front_y, back_x, back_y):
    dx = front_x - back_x
    dy = front_y - back_y
    return math.degrees(math.atan2(dy, dx))


def fetch_frame():
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


def update_chariots(x, y, angle):
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


def process_inference(frame, data):
    global amount_robots_seen
    if frame is None or data is None:
        print("no frame or no data")
        return None
    bottom_x, bottom_y = None, None
    top_x, top_y = None, None

    # er is altijd maar 1 element
    for element in data:
        count = 0
        amount_robots_seen = len(element["predictions"])
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

            update_chariots(x, y, angle)

    return frame



processed_frame = None


def getchariots():
    global processed_frame

    frame = fetch_frame()

    data = infer_frame(frame)

    # for with view
    processed_frame = process_inference(frame, data)
    # for without view
    # processed_frame = None
    # process_inference_noview(data)
    # print(f"camera detected chariots: {camera_chariots}")

    # print("Camera got frame succesfully")

    return camera_chariots


def camera_view():
    global processed_frame

    while True:
        if processed_frame is not None:
            print(processed_frame)
            cv2.imshow("Camera", processed_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        sleep(1)


def main():
    while True:
        frame = fetch_frame()
        data = infer_frame(frame)

        # for with view
        processed_frame = process_inference(frame, data)

        # for without view
        # processed_frame = None
        # process_inference_noview(data)

        print(camera_chariots)
        if processed_frame is not None:
            cv2.imshow("Camera", processed_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
