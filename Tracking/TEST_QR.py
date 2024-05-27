import cv2
import numpy as np 

img = cv2.imread('qrcode/qrcode_test_1.png')
qcd = cv2.QRCodeDetector()
retval, decoded_info, points, straight_qrcode = qcd.detectAndDecodeMulti(img)

def QRcodePR(points):
    x = 0.5*(points[2][0] + points[0][0])
    y = 0.5*(points[2][1] + points[0][1])
    middelpunt = (x,y)

    #rotatie van de qrcode
    vector = points[1] - points[0]
    angle = np.arctan2(vector[1], vector[0]) * 180 / np.p
    
    if angle < 0:
        angle += 360
    return (middelpunt, angle)

if (retval != False):
        print(decoded_info)
        # ('QR Code Two', '', 'QR Code One')
        match(len(points)):
            case 0:
                print("No QR-code found")
            case 1:
                points = points[0]
                # Bereken de hoek van rotatie
                vector = points[1] - points[0]
                angle = np.arctan2(vector[1], vector[0]) * 180 / np.pi

                # Zorg ervoor dat de hoek in het bereik van 0 tot 360 graden valt
                if angle < 0:
                    angle += 360
                print(angle)
            case 2:
                x1 = 0.5*(points[0][2][0] + points[0][0][0])
                y1 = 0.5*(points[0][2][1] + points[0][0][1])
                middelpunt1 = (x1,y1)
                print(middelpunt1)

                x2 = 0.5*(points[1][2][0] + points[1][0][0])
                y2 = 0.5*(points[1][2][1] + points[1][0][1])
                middelpunt2 = (x2,y2)
                print(middelpunt2)
            case _:
                print("huh")

