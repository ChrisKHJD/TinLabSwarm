import requests 
import cv2
import numpy as np 
import imutils

# Replace the below URL with your own. Make sure to add "/shot.jpg" at last. 
url = "http://145.24.238.116:8080/shot.jpg"

def QRcodePR(points):
    #middelpunt van de qrcode
    x = 0.5*(points[2][0] + points[0][0])
    y = 0.5*(points[2][1] + points[0][1])
    middelpunt = (x,y)

    #rotatie van de qrcode
    vector = points[1] - points[0]
    angle = np.arctan2(vector[1], vector[0]) * 180 / np.pi

    if angle < 0:
        angle += 360
    return (middelpunt, angle)

while True:
    img_resp = requests.get(url) 
    img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8) 
    img = cv2.imdecode(img_arr, -1)
    #img = imutils.resize(img, width=3840, height=2160)
    qcd = cv2.QRCodeDetector()
    retval, decoded_info, points, straight_qrcode = qcd.detectAndDecodeMulti(img)
    
    if (retval != False):
        print(decoded_info)
        
        aantal_qr = len(points)

        while aantal_qr > 0:
            first = len(points) - aantal_qr
            print(QRcodePR(points[first]))
            aantal_qr -= 1

        # match(len(points)):
        #     case 0:
        #         print("No QR-code found")
        #     case 1:
        #         print(QRcodePR(points[0]))
        #     case 2:
        #         print(QRcodePR(points[0]))
        #         print(QRcodePR(points[1]))
        #     case _:
        #         print("huh")
    # Press Esc key to exit 
    if cv2.waitKey(1) == 27: 
        break


cv2.destroyAllWindows() 

# print(points)
# # [[[290.9108    106.20954  ]
# #   [472.8162      0.8958926]
# #   [578.5836    184.1002   ]
# #   [396.0495    287.81277  ]]
# # 
# #  [[620.         40.       ]
# #   [829.         40.       ]
# #   [829.        249.       ]
# #   [620.        249.       ]]
# # 
# #  [[ 40.         40.       ]
# #   [249.         40.       ]
# #   [249.        249.       ]
# #   [ 40.        249.       ]]]

# print(points.shape)
# # (3, 4, 2)

# print(type(straight_qrcode))
# # <class 'tuple'>

# print(type(straight_qrcode[0]))
# # <class 'numpy.ndarray'>

# print(straight_qrcode[0].shape)
# # (21, 21)

# img = cv2.polylines(img, points.astype(int), True, (0, 255, 0), 3)

# for s, p in zip(decoded_info, points):
#     img = cv2.putText(img, s, p[0].astype(int),
#                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

# cv2.imwrite('qrcode/qrcode_opencv.jpg', img)
# # True