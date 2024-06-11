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
            angle = calculate_angle(top_x, top_y, bottom_x, bottom_y)

            update_chariots(x, y, angle)

    return frame