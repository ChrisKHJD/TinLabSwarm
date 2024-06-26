import cv2
import json
import math
import requests
import numpy as np
import imutils
from inference import get_model
from time import sleep

CAMERA_URL = "http://145.137.117.192:8080//shot.jpg"
MODEL_ID = "robot-location-and-orientation/1"
APIKEY = "CnyYmNzp3FktcouTB3d5"
FRAME_WIDTH = 960
FRAME_HEIGHT = 540

model = get_model(model_id=MODEL_ID, api_key=APIKEY)
camera_chariots = {}
amount_robots_seen = 0


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
    global camera_chariots
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
            width = int(prediction["width"])
            height = int(prediction["height"])

            x1 = int(x - (width / 2))
            y1 = int(y - (height / 2))
            x2 = int(x + (width / 2))
            y2 = int(y + (height / 2))

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            for keypoint in prediction["keypoints"]:
                keypoint_x = int(keypoint["x"])
                keypoint_y = int(keypoint["y"])
                class_name = keypoint["class_name"]
                if class_name == "top":
                    color = (0, 0, 255)
                    top_x, top_y = keypoint_x, keypoint_y
                elif class_name == "bottom":
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
    global amount_robots_seen
    if data is None:
        print("no data")
        return None

    # Since there is always only one element in data
    for element in data:
        amount_robots_seen = 0
        for prediction in element["predictions"]:
            x = int(prediction["x"])
            y = int(prediction["y"])
            amount_robots_seen += 1
            top_x, top_y, bottom_x, bottom_y = None, None, None, None

            for keypoint in prediction["keypoints"]:
                keypoint_x = int(keypoint["x"])
                keypoint_y = int(keypoint["y"])
                class_name = keypoint["class_name"]

                if class_name == "top":
                    top_x, top_y = keypoint_x, keypoint_y
                elif class_name == "bottom":
                    bottom_x, bottom_y = keypoint_x, keypoint_y

            if (
                top_x is not None
                and top_y is not None
                and bottom_x is not None
                and bottom_y is not None
            ):
                # Calculate the angle between top and bottom keypoints
                angle = calculate_angle(bottom_x, bottom_y, top_x, top_y)

                # Update chariots with the calculated angle
                update_chariots(x, y, angle)


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


def calculate_angle(x1, y1, x2, y2):
    calculated_angle = math.degrees(math.cos(y2 - y1, x2 - x1))
    # if calculated_angle < 0:
    #     return 360 + calculated_angle
    # else:
    return calculated_angle


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

        target_angle = calculate_angle(
            camera_chariots[0][0],
            camera_chariots[0][1],
            camera_chariots[1][0],
            camera_chariots[1][1],
        )

        print(f"target angle: {target_angle}")

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
