import json
import cv2
import math
import imutils
import time
import numpy as np
from inference import get_model

MODELID = "swarmkeypoint/1"
APIKEY = "CnyYmNzp3FktcouTB3d5"
IMAGE_PATH = "testimage.jpg"
FRAME_WIDTH = 1920 #640
FRAME_HEIGHT = 1080 #480
model = get_model(model_id=MODELID, api_key=APIKEY)


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
        img = cv2.imread(IMAGE_PATH)
        if img is None:
            raise FileNotFoundError(f"Image not found at path: {IMAGE_PATH}")

        resized_frame = imutils.resize(img, width=FRAME_WIDTH, height=FRAME_HEIGHT)
        return resized_frame
    except Exception as e:
        print("Error fetching frame:", e)
        return None
# def fetch_frame():
#     try:
#         img = cv2.imread(IMAGE_PATH)
#         img_arr = np.array(bytearray(img.content), dtype=np.uint8)
#         frame = cv2.imdecode(img_arr, -1)
#         return imutils.resize(frame, width=FRAME_WIDTH, height=FRAME_HEIGHT)
#     except Exception as e:
#         print("Error fetching frame:", e)
#         return None

def infer_frame(frame):
    try:
        response = model.infer(frame)
        json_data = json.dumps([ob.__dict__ for ob in response], default=lambda x: x.__dict__)
        data = json.loads(json_data)
        return data
    except Exception as e:
        print("Error during inference:", e)
        return None


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

    return frame


def main():
    frame = fetch_frame()
    data = infer_frame(frame)
    processed_frame = process_inference(frame, data)

    cv2.imshow('Picture', processed_frame)
    # Wait for 5000 milliseconds (5 seconds)
    while True:
        key = cv2.waitKey(1) & 0xFF  # Wait for 1ms for a key event
        if key == ord('q'):  # Check if the pressed key is 'q'
            break  # Exit the loop if 'q' is pressed

        # Close the OpenCV window
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
