import socket
import network
import time
import ujson as json
import utime as time_lib
from machine import Pin, PWM

# Constants
BUILT_IN_LED = 25
FLED = 20
BLED = 21
PWM_LM = 6
PWM_RM = 7
PWM_SC = 10
SDA = 4
SCL = 5
MISO = 16
MOSI = 19
SCK = 18
CS = 17

# Constants for movement directions
FORWARD = 'forward'
BACKWARD = 'backward'
LEFT = 'left'
RIGHT = 'right'

# Insert your network parameters
SSID = b'ssid' 
PWD = b'pwd' 

# Robot ID constant
ROBOT_ID = "RB1"

class RobotController:
    def __init__(self):
        self.setup_pins()
        self.setup_servos()
        self.setup_network()

    def setup_pins(self):
        self.built_in_led = Pin(BUILT_IN_LED, Pin.OUT)
        self.fled = Pin(FLED, Pin.OUT)
        self.bled = Pin(BLED, Pin.OUT)
        
    def handle_emergency_stop(self):
        # Stop all movements and blink LEDs
        self.LeftMotor.duty_u16(0)
        self.RightMotor.duty_u16(0)
        self.PanMotor.duty_u16(0)
        self.blink_leds()
        
    def blink_leds(self):
        # Blink the front and back LEDs
        for _ in range(5):  # Blink 5 times
            self.fled.value(not self.fled.value())  # Toggle front LED
            self.bled.value(not self.bled.value())  # Toggle back LED
            time.sleep(0.5)  # 0.5 second delay between blinks
        
    def setup_servos(self):
        self.LeftMotor = PWM(Pin(PWM_LM))
        self.LeftMotor.freq(50)
        self.RightMotor = PWM(Pin(PWM_RM))
        self.RightMotor.freq(50)
        self.PanMotor = PWM(Pin(PWM_SC))
        self.PanMotor.freq(50)

    def setup_network(self):
        network.hostname("mypicow")
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)

    def move_forward(self, power, time):
        self.LeftMotor.duty_u16(7000)
        self.RightMotor.duty_u16(3000)
        time.sleep(time)
        self.LeftMotor.duty_u16(5000)
        self.RightMotor.duty_u16(5000)
    
    def move_robot(self, direction):
        if direction == FORWARD:
            self.built_in_led.value(1)
            self.fled.value(1)
            self.built_in_led.value(0)
            self.fled.value(0)
            print(f"{time_lib.localtime()} - Robot {ROBOT_ID} moving forward")
        elif direction == BACKWARD:
            self.built_in_led.value(1)
            self.bled.value(1)
            self.built_in_led.value(0)
            self.bled.value(0)
            print(f"{time_lib.localtime()} - Robot {ROBOT_ID} moving backward")
        elif direction == LEFT:
            self.built_in_led.value(1)
            self.built_in_led.value(0)
            print(f"{time_lib.localtime()} - Robot {ROBOT_ID} moving left")
        elif direction == RIGHT:
            self.built_in_led.value(1)
            self.built_in_led.value(0)
            print(f"{time_lib.localtime()} - Robot {ROBOT_ID} moving right")

        print(f"{time_lib.localtime()} - Robot {ROBOT_ID} moved:", direction)
        
    def handle_coordinates(self, coordinates):
        print(f"{time_lib.localtime()} - Received coordinates for {ROBOT_ID}:", coordinates)
    
    def connect_wifi(self):
        time0 = time_lib.time()
        self.wlan.connect(SSID, PWD)
        while True:
            if self.wlan.isconnected():
                print("\nConnected!\n")
                self.built_in_led.value(True)
                print("IP Address:", self.wlan.ifconfig()[0])
                break
            else:
                print(".")
                time_lib.sleep(1)
                if time_lib.time() - time0 > 10:
                    print("Connection could not be established")
                    break

    def serve_requests(self):
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        print("Listening to port 80\n")
        s.listen(1)
        
        while True:
            cl, addr = s.accept()
            print("Incoming connection request from: " + str(addr) + "\n")
            cl_file = cl.makefile('rwb', 0)
            found = False
            while True:
                line = cl_file.readline()
                if not line or line == b'\r\n':
                    break
                if not found:
                    if str(line).find("/?PRESS=FRONT_LED_ON") != -1:
                        self.fled.value(True)
                        found = True
                    if str(line).find("/?PRESS_1=FRONT_LED_OFF") != -1:
                        self.fled.value(False)
                        found = True
                    if str(line).find("/?PRESS_2=BACK_LED_ON") != -1:
                        self.bled.value(True)
                        found = True
                    if str(line).find("/?PRESS_3=BACK_LED_OFF") != -1:
                        self.bled.value(False)
                        found = True
                    if str(line).find("/?PRESS_4=MOVE") != -1:
                        self.move_forward(50, 1)
                        found = True
                    if str(line).find("/emergency_stop") != -1:
                        self.handle_emergency_stop()
                        found = True
                    if str(line).find("/coordinates") != -1:
                        data = line.split(b' ')[1]
                        coordinates = json.loads(data)
                        self.handle_coordinates(coordinates)
                        found = True

            try:
                response = "HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n" + open("main.html", "r").read()
            except:
                response = "HTTP/1.0 404 Not Found\r\n\r\n"
            cl.send(response)
            cl.close()

def main():
    robot = RobotController()
    robot.connect_wifi()
    robot.serve_requests()

if __name__ == "__main__":
    main()
