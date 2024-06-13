import cv2
import json
import math
import requests
import numpy as np
import imutils
from inference import get_model
from time import sleep
import time

CAMERA_URL = "http://145.24.243.14:8080//shot.jpg"
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


def update_chariots(robot_positions):
    global camera_chariots, amount_robots_seen
    if len(camera_chariots) < len(robot_positions):
        for robot_id, (robot_x, robot_y, _) in camera_chariots.items():
            (nearest_x, nearest_y, nearest_angle) = (0,0,0)
            min_distance = float("inf")
            #loop door de robot posities die binnen komen en kies de dichtbijzijnste
            if len(robot_positions) > 0:
                for x, y, angle in robot_positions:
                    distance = math.sqrt((x - robot_x) ** 2 + (y - robot_y) ** 2)
                    if distance < min_distance:
                        min_distance = distance
                        (nearest_x, nearest_y, nearest_angle) = (x, y, angle)
                camera_chariots[robot_id] = (nearest_x, nearest_y, nearest_angle)
                print(f"robot_positions: {robot_positions}, nearestX: {nearest_x}, nearestY: {nearest_y}, nearestAngle: {nearest_angle}")
                robot_positions.remove((nearest_x, nearest_y, nearest_angle))
        #add the remaining robots
        for new_x, new_y, new_angle in robot_positions:
            camera_chariots[len(camera_chariots)] = (new_x, new_y, new_angle)
    elif len(camera_chariots) > len(robot_positions):
        id_list = []
        for x, y, angle in robot_positions:
            nearest_robot_id = None
            min_distance = float("inf")
            for robot_id, (robot_x, robot_y, _) in camera_chariots.items():
                distance = math.sqrt((x - robot_x) ** 2 + (y - robot_y) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    nearest_robot_id = robot_id
            camera_chariots[nearest_robot_id] = (x, y, angle)
            id_list.append(nearest_robot_id)
        #welke van camera_chartiots is over? die removen
        # for robot_id, (robot_x, robot_y, _) in camera_chariots.items():
        #     if not (robot_id in id_list):
        #         camera_chariots.pop(robot_id)
        camera_chariots = {robot_id: (robot_x, robot_y, angle) for robot_id, (robot_x, robot_y, angle) in
                           camera_chariots.items() if robot_id in id_list}
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

def process_inference(frame, data):
    global amount_robots_seen
    if frame is None or data is None:
        print("no frame or no data")
        return None
    bottom_x, bottom_y = None, None
    top_x, top_y = None, None

    # er is altijd maar 1 element
    for element in data:
        update_chariots_list = []
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
            angle = calculate_angle(top_x, top_y, bottom_x, bottom_y)

            update_chariots_list.append((x, y, angle))
        update_chariots(update_chariots_list)

    return frame

def main():
    frame_counter = 0
    start_time = time.time()

    while True:
        frame = fetch_frame()
        data = infer_frame(frame)

        processed_frame = process_inference(frame, data)



        # Calculate elapsed time and add frame
        frame_counter += 1
        elapsed_time = time.time() - start_time

        # Print frames processed per second every second
        if elapsed_time >= 1.0:
            print(f"Frames processed in the last second: {frame_counter}")
            frame_counter = 0
            start_time = time.time()

        print(camera_chariots)
        if processed_frame is not None:
            cv2.imshow("Camera", processed_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
