import socket
import network
import time
from machine import Pin, PWM
import json
from time import sleep

# Constants
BUILT_IN_LED_PIN = 25
FLED_PIN = 20
BLED_PIN = 21
PWM_LM_PIN = 6
PWM_RM_PIN = 7
PWM_SC_PIN = 10
SDA_PIN = 4
SCL_PIN = 5
MISO_PIN = 16
MOSI_PIN = 19 
SCK_PIN = 18
CS_PIN = 17

SSID = b'tesla iot' 
PASSWORD = b'fsL6HgjN' 
PORT = 8000
IP_ADDRESS = "145.137.55.132" # 145.24.223.115, temp: 145.137.55.132
TIMEOUT_VALUE = 0.1

# PWM Frequencies and Duty Cycles
PWM_FREQUENCY = 50
DUTY_CYCLE_STOP = 0
DUTY_CYCLE_FORWARD_LEFT = 6000
DUTY_CYCLE_FORWARD_RIGHT = 3050
DUTY_CYCLE_BACKWARD_LEFT = 3000
DUTY_CYCLE_BACKWARD_RIGHT = 7000

class RobotController:
    def __init__(self):
        self.setup_pins()
        self.setup_servos()
        self.setup_network()
        self.last_send_time = time.time()
        self.s = None  
        self.instruction_handlers = {
            "move": self.test_move,
            "move_forward": self.move_forward,
            "move_backward": self.move_backward,
            "turn_left": self.turn_left,
            "turn_right": self.turn_right,
            "stop": self.emergency_stop,
            "led_blink": self.blink_leds,
            "led_on": self.turn_led_on,
            "led_off": self.turn_led_off
        }
        self.html_page = """
        <html>
            <head>
                <title>Robot Controller</title>
            </head>
            <body>
                <h1>Robot Controller</h1>
                <button onclick="sendRequest('/?PRESS=FRONT_LED_ON')">Front LED On</button>
                <button onclick="sendRequest('/?PRESS_1=FRONT_LED_OFF')">Front LED Off</button>
                <button onclick="sendRequest('/?PRESS_2=BACK_LED_ON')">Back LED On</button>
                <button onclick="sendRequest('/?PRESS_3=BACK_LED_OFF')">Back LED Off</button>
                <button onclick="sendRequest('/?PRESS_4=MOVE_FORWARD')">Move Forward</button>
                <button onclick="sendRequest('/?PRESS_5=MOVE_BACKWARD')">Move Backward</button>
                <button onclick="sendRequest('/?PRESS_6=TURN_LEFT')">Turn Left</button>
                <button onclick="sendRequest('/?PRESS_7=TURN_RIGHT')">Turn Right</button>
                <button onclick="sendRequest('/?PRESS_8=STOP')">Stop</button>
                <button onclick="sendRequest('/?PRESS_9=TEST')">Test</button>
                <script>
                    function sendRequest(url) {
                        var xhr = new XMLHttpRequest();
                        xhr.open("GET", url, true);
                        xhr.send();
                    }
                </script>
            </body>
        </html>
        """

    def setup_pins(self):
        self.built_in_led = Pin(BUILT_IN_LED_PIN, Pin.OUT)
        self.fled = Pin(FLED_PIN, Pin.OUT)
        self.bled = Pin(BLED_PIN, Pin.OUT) 

    def setup_servos(self):
        self.LeftMotor = PWM(Pin(PWM_LM_PIN))
        self.LeftMotor.freq(PWM_FREQUENCY)
        self.RightMotor = PWM(Pin(PWM_RM_PIN))
        self.RightMotor.freq(PWM_FREQUENCY)
        self.PanMotor = PWM(Pin(PWM_SC_PIN))
        self.PanMotor.freq(PWM_FREQUENCY)

    def setup_network(self):
        network.hostname("mypicow")
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
    def blink_leds(self, times=5, interval=0.5):    
        for _ in range(times):
            self.fled.value(not self.fled.value())
            self.bled.value(not self.bled.value())
            time.sleep(interval)
            print(f"Blinking LEDs on pins {self.fled} and {self.bled}")


    def turn_led_on(self, pin=BUILT_IN_LED_PIN):
        led = Pin(pin, Pin.OUT)
        led.value(True)
        print(f"LED on pin {pin} is now ON")

    def turn_led_off(self, pin=BUILT_IN_LED_PIN):
        led = Pin(pin, Pin.OUT)
        led.value(False)
        print(f"LED on pin {pin} is now OFF")

    def emergency_stop(self):
        self.LeftMotor.duty_u16(DUTY_CYCLE_STOP)
        self.RightMotor.duty_u16(DUTY_CYCLE_STOP)
        self.blink_leds(BUILT_IN_LED_PIN)
        print("Emergency Stop")

    def move_forward(self):
        self.LeftMotor.duty_u16(DUTY_CYCLE_FORWARD_LEFT)
        self.RightMotor.duty_u16(DUTY_CYCLE_FORWARD_RIGHT)
        print("Moving Forward")

    def move_backward(self):
        self.LeftMotor.duty_u16(DUTY_CYCLE_BACKWARD_LEFT)
        self.RightMotor.duty_u16(DUTY_CYCLE_BACKWARD_RIGHT)
        print("Moving Backward")

    def turn_left(self):
        self.LeftMotor.duty_u16(DUTY_CYCLE_STOP)
        self.RightMotor.duty_u16(DUTY_CYCLE_FORWARD_RIGHT)
        print("Turning Left")

    def turn_right(self):
        self.LeftMotor.duty_u16(DUTY_CYCLE_FORWARD_LEFT)
        self.RightMotor.duty_u16(DUTY_CYCLE_STOP)
        print("Turning Right")

    def test_move(self):
        self.move_forward()
        time.sleep(1)
        self.emergency_stop()
        time.sleep(1)
        self.turn_left()
        time.sleep(1)
        self.emergency_stop()
        time.sleep(1)
        self.turn_right()
        time.sleep(1)
        self.emergency_stop()
        time.sleep(1)
        self.move_forward()
        time.sleep(3)
        self.emergency_stop()
        time.sleep(1)
        self.move_backward()
        time.sleep(3)
        self.emergency_stop()
        print("Test Move Completed")

    def send_data(self):
        try:
            if not self.s:
                self.create_socket()

            payload = {"type": "chariot"}
            encoded_payload = json.dumps(payload).encode("ascii")
            self.s.sendall(encoded_payload)
            print(f"Sent payload: {payload}")
        except Exception as e:
            print(f"Error sending data: {e}")

    def receive_data(self):
        try:
            if not self.s:
                self.create_socket()

            received_data = self.s.recv(1024).decode()
            if received_data:
                print(f"Received: {received_data}")
                data = json.loads(received_data)
                instruction = data.get("instruction")
                if instruction in self.instruction_handlers:
                    self.instruction_handlers[instruction]()
                else:
                    print(f"Unknown instruction: {instruction}")
                return True
            else:
                print("No data received")
                return False
        except Exception as e:
            print(f"Error receiving data: {e}")
            return False

    def create_socket(self):
        try:
            self.s = socket.socket()
            self.s.connect((IP_ADDRESS, PORT))
            self.s.settimeout(TIMEOUT_VALUE)
            print("Socket created and connected")
        except Exception as e:
            print(f"Connection failed: {e}")
            self.s = None

    def connect_wifi(self):
        start_time = time.time()
        self.wlan.connect(SSID, PASSWORD)
        while not self.wlan.isconnected():
            print(".")
            time.sleep(1)
            if time.time() - start_time > 10:
                print("Connection could not be established")
                return
        print("Connected to WiFi")
        self.built_in_led.value(True)
        print("IP Address:", self.wlan.ifconfig()[0])

    def serve_requests(self):
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(addr)
        print("Listening on port 80")
        server_socket.listen(1)

        while True:
            client, addr = server_socket.accept()
            print(f"Incoming connection from {addr}")
            client_file = client.makefile('rwb', 0)
            found = False
            while True:
                line = client_file.readline()
                if not line or line == b'\r\n':
                    break
                if not found:
                    if b"/?PRESS=FRONT_LED_ON" in line:
                        self.turn_led_on(FLED_PIN)
                        found = True
                    if b"/?PRESS_1=FRONT_LED_OFF" in line:
                        self.turn_led_off(FLED_PIN)
                        found = True
                    if b"/?PRESS_2=BACK_LED_ON" in line:
                        self.turn_led_on(BLED_PIN)
                        found = True
                    if b"/?PRESS_3=BACK_LED_OFF" in line:
                        self.turn_led_off(BLED_PIN)
                        found = True
                    if b"/?PRESS_4=MOVE" in line:
                        self.move_forward()
                        found = True
                    if b"/?PRESS_5=MOVE_BACKWARD" in line:
                        self.move_backward()
                        found = True
                    if b"/?PRESS_6=TURN_LEFT" in line:
                        self.turn_left()
                        found = True
                    if b"/?PRESS_7=TURN_RIGHT" in line:
                        self.turn_right()
                        found = True
                    if b"/?PRESS_8=STOP" in line:
                        self.emergency_stop()
                        found = True
                    if b"/?PRESS_9=TEST" in line:
                        self.test_move()
                        found = True

            response = "HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n" + self.html_page
            client.send(response)
            client.close()

    def main_loop(self):
        while True:
            try:
                if time.time() - self.last_send_time >= 1:
                    self.send_data()
                    self.last_send_time = time.time()

                if self.receive_data():
                    pass

            except Exception as e:
                print(f"Error: {e}")

            sleep(0.5)

def main():
    robot = RobotController()
    robot.connect_wifi()
    robot.main_loop()
    # robot.serve_requests() # Voor Het Testen

if __name__ == "__main__":
    main()

