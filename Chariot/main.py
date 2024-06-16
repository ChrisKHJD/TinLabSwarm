"""
Robot Controller Script for Raspberry Pi Pico W

This script is designed to control a robot using a Raspberry Pi Pico W. 
It connects to a Wi-Fi network, establishes a socket connection to send and receive data, 
and provides a web interface for user interaction. The robot can perform various actions 
such as moving forward, backward, rotating, and stopping. Additionally, it can control 
LEDs and handle emergency stop commands.

Key Components:
- Constants: Defines pin numbers, network credentials, and PWM settings.
- RobotController Class: Manages the robot's movements, LED controls, network connection, 
  and web server.
- Main Loop: Periodically sends data to a server and processes incoming commands.

Functionality:
1. LED Control: Turn on/off front and back LEDs, and blink LEDs for emergency stops.
2. Movement Control: Move forward, backward, turn left, right, and stop the robot.
3. Network Communication: Connect to a specified Wi-Fi network and communicate with a server.
4. Web Interface: Provides a simple HTML page to control the robot via HTTP requests.
5. Emergency Handling: Immediate stop and LED blink in case of an emergency.

Usage:
- Configure the constants as needed (e.g., Wi-Fi credentials, IP address).
- Create a RobotController instance and call the `connect_wifi()` method to connect to Wi-Fi.
- Use the `main_loop()` method to start the robot's operation, periodically sending and receiving data.
- Optionally, call `serve_requests()` to start the web server for remote control.

"""

import network
import time
from machine import Pin, PWM
import json
from time import sleep
import ubinascii
import socket

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

SSID = b'iotroam' # tesla iot, 
PASSWORD = b'Robot!!/#' # fsL6HgjN, 
PORT = 8000
IP_ADDRESS = "145.24.243.10" # 145.24.223.115, temp: 145.137.55.132
TIMEOUT_VALUE = 0.1 

# PWM Frequencies and Duty Cycles 
PWM_FREQUENCY = 50 
DUTY_CYCLE_STOP = 0 
DUTY_CYCLE_FORWARD_LEFT = 5100  # 5050 6050  5150 |Black:5100  |Red:5100  |Blue:5290 
DUTY_CYCLE_FORWARD_RIGHT = 4516 # 4450 3050  4550 |Black:4525  |Red:4516  |Blue:5130 
DUTY_CYCLE_BACKWARD_LEFT = 4516 # 4450 3000  4550 |Black:4525  |Red:4516  |Blue:4450 
DUTY_CYCLE_BACKWARD_RIGHT = 5100 # 5050 7000 5150 |Black:5150  |Red:5100  |Blue:4530 



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
            "rotate_left": self.turn_left,
            "rotate_right": self.turn_right,
            "stop": self.stop,
            "emergency_stop":self.emergency_stop,
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
        self.turn_led_on(FLED_PIN)  # Ensure front LED is on
        self.turn_led_on(BLED_PIN)  # Ensure back LED is on
        self.turn_led_on(BUILT_IN_LED_PIN)  # Ensure built-in LED is on

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
        initial_fled_state = self.fled.value()
        initial_bled_state = self.bled.value()
        
        for _ in range(times):
            self.fled.value(not self.fled.value())
            self.bled.value(not self.bled.value())
            time.sleep(interval)
            print(f"Blinking LEDs on pins {self.fled} and {self.bled}")
        
        # Restore the initial state of the LEDs
        self.fled.value(initial_fled_state)
        self.bled.value(initial_bled_state)

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
    
    def stop(self):
        self.LeftMotor.duty_u16(5000) # Zwart-Chariot: 5000, Red-Chariot: 5000, Blue-Chariot: 4920 (Verschil:160)
        self.RightMotor.duty_u16(5000) # Zwart-Chariot: 4950(Verschil 50), Red-Chariot: 5000, Blue-Chariot:5000 
        print("Stop")

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
        time.sleep(2)
        self.stop()
        time.sleep(2)
        self.turn_left()
        time.sleep(2)
        self.stop()
        time.sleep(2)
        self.turn_right()
        time.sleep(2)
        self.stop()
        time.sleep(2)
        self.move_forward()
        time.sleep(2)
        self.stop()
        time.sleep(2)
        self.move_backward()
        time.sleep(0.5)
        self.stop()
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

def get_mac_address():
    wlan = network.WLAN(network.STA_IF)  # Get WLAN interface object
    wlan.active(True)  # Activate WLAN interface
    mac_address = wlan.config('mac')  # Get MAC address
    mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
    return mac_address, mac

        


def main():
    robot = RobotController()
    robot.connect_wifi()
    #robot.serve_requests()
    robot.main_loop()
    
    #robot.move_forward()
    #robot.move_backward()
    #robot.test_move()
    
    # Call the function to get and print the MAC address
    #print("MAC Address:", get_mac_address())
    

if __name__ == "__main__":
    main()
