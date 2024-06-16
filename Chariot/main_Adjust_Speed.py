'''
Calculate Speed Difference , Increase & Decrease Speed.
Needs More Testing....
'''

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

SSID = b'iotroam'
PASSWORD = b'Robot!!/#'
PORT = 8000
IP_ADDRESS = "145.24.243.16"
TIMEOUT_VALUE = 0.1 

# PWM Frequencies and Duty Cycles 
PWM_FREQUENCY = 50 
DUTY_CYCLE_STOP = 0 

LEFT_SERVO = 5100 # |Black:5100  |Red:5100  |Blue:5290 
RIGHT_SERVO = 4516 # |Black:4525  |Red:4516  |Blue:5130
'''
DUTY_CYCLE_FORWARD_LEFT = 5100  # 5050 6050  5150 |Black:5100  |Red:5100  |Blue:5290 
DUTY_CYCLE_FORWARD_RIGHT = 4516 # 4450 3050  4550 |Black:4525  |Red:4516  |Blue:5130 
DUTY_CYCLE_BACKWARD_LEFT = 4516 # 4450 3000  4550 |Black:4525  |Red:4516  |Blue:4450 
DUTY_CYCLE_BACKWARD_RIGHT = 5100 # 5050 7000 5150 |Black:5150  |Red:5100  |Blue:4530
'''
# Speed difference between left and right motors for straight movement
SPEED_DIFFERENCE = LEFT_SERVO - RIGHT_SERVO  # 
print("Speed Difference: ", SPEED_DIFFERENCE)

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
            "rotate_end_right": self.turn_right,
            "stop": self.stop,
            "emergency_stop": self.emergency_stop,
            "led_blink": self.blink_leds,
            "led_on": self.turn_led_on,
            "led_off": self.turn_led_off
        }

    def compute_speed(self, distance):
        max_distance = 100  
        min_speed = 5100  # |BLACK:5100 |BLUE: |RED:  
        max_speed = 4050  # |BLACK:4050 |BLUE: |RED:  
        clamped_distance = max(0, min(distance, max_distance))
        speed = max_speed - (clamped_distance / max_distance * (max_speed - min_speed))
        return int(speed)

    def setup_pins(self):
        self.built_in_led = Pin(BUILT_IN_LED_PIN, Pin.OUT)
        self.fled = Pin(FLED_PIN, Pin.OUT)
        self.bled = Pin(BLED_PIN, Pin.OUT)
        self.turn_led_on(FLED_PIN)  
        self.turn_led_on(BLED_PIN)  
        self.turn_led_on(BUILT_IN_LED_PIN)  

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
        self.blink_leds()
        print("Emergency Stop")

    def stop(self):
        self.LeftMotor.duty_u16(5000) # Zwart-Chariot: 5000, Red-Chariot: 5000, Blue-Chariot: 4920 (Verschil:160) 
        self.RightMotor.duty_u16(5000)  # Zwart-Chariot: 4950(Verschil 50), Red-Chariot: 5000, Blue-Chariot:5000
        print("Stop")

    def move_forward(self, speed):
        left_motor_speed = max(int(speed * 0.5), 2000)  # Calculate base speed
        right_motor_speed = left_motor_speed + SPEED_DIFFERENCE  # Apply differential for straight movement
        self.LeftMotor.duty_u16(left_motor_speed)
        self.RightMotor.duty_u16(right_motor_speed)
        print(f"Moving Forward - Left speed: {left_motor_speed}, Right speed: {right_motor_speed}")

    def move_backward(self, speed):
        left_motor_speed = max(int(speed * 0.5), 2000)  # Calculate base speed
        right_motor_speed = left_motor_speed + SPEED_DIFFERENCE  # Apply differential for straight movement
        self.LeftMotor.duty_u16(left_motor_speed)
        self.RightMotor.duty_u16(right_motor_speed)
        print(f"Moving Backward - Left speed: {left_motor_speed}, Right speed: {right_motor_speed}")

    def turn_left(self, speed):
        turn_speed = max(int(speed * 0.5), 2000)
        self.LeftMotor.duty_u16(DUTY_CYCLE_STOP)
        self.RightMotor.duty_u16(turn_speed)
        print(f"Turning Left at speed: {turn_speed}")

    def turn_right(self, speed):
        turn_speed = max(int(speed * 0.5), 2000)
        self.LeftMotor.duty_u16(turn_speed)
        self.RightMotor.duty_u16(DUTY_CYCLE_STOP)
        print(f"Turning Right at speed: {turn_speed}")

    def test_move(self):
        # Testing sequence of movements
        self.move_forward(4000)
        sleep(2)
        self.stop()
        sleep(2)
        self.turn_left(4000)
        sleep(2)
        self.stop()
        sleep(2)
        self.turn_right(4000)
        sleep(2)
        self.stop()
        sleep(2)
        self.move_backward(4000)
        sleep(0.5)
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
                distance = data.get("distance", 100)

                speed = self.compute_speed(distance)

                if instruction in self.instruction_handlers:
                    handler = self.instruction_handlers[instruction]
                    if instruction in {"move_forward", "move_backward", "rotate_left", "rotate_right"}:
                        handler(speed)
                    else:
                        handler()
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

        try:
            while True:
                client, addr = server_socket.accept()
                print(f"Incoming connection from {addr}")
                client_file = client.makefile('rwb', 0)
                try:
                    found = False
                    while True:
                        line = client_file.readline()
                        if not line or line == b'\r\n':
                            break
                        if not found:
                            # Default speed for demo purposes
                            default_speed = 4000
                            command_map = {
                                b"/?PRESS=FRONT_LED_ON": lambda: self.turn_led_on(FLED_PIN),
                                b"/?PRESS_1=FRONT_LED_OFF": lambda: self.turn_led_off(FLED_PIN),
                                b"/?PRESS_2=BACK_LED_ON": lambda: self.turn_led_on(BLED_PIN),
                                b"/?PRESS_3=BACK_LED_OFF": lambda: self.turn_led_off(BLED_PIN),
                                b"/?PRESS_4=MOVE": lambda: self.move_forward(default_speed),
                                b"/?PRESS_5=MOVE_BACKWARD": lambda: self.move_backward(default_speed),
                                b"/?PRESS_6=TURN_LEFT": lambda: self.turn_left(default_speed),
                                b"/?PRESS_7=TURN_RIGHT": lambda: self.turn_right(default_speed),
                                b"/?PRESS_8=STOP": self.emergency_stop,
                                b"/?PRESS_9=TEST": self.test_move
                            }

                            for key, function in command_map.items():
                                if key in line:
                                    function()
                                    found = True
                                    break

                    if not found:
                        print("No valid command found")

                finally:
                    response = "HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n" + self.html_page
                    client.send(response)
                    client.close()
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            server_socket.close()
            print("Server shutdown")

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
    robot.main_loop()

if __name__ == "__main__":
    main()
    
