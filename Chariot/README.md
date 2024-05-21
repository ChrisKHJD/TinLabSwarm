# Robot Controller Documentation

This documentation provides an overview and guide on how to use the Python and HTML code to control a robot with a Raspberry Pi Pico W. The system allows control of front and back LEDs, movement, and an emergency stop function through a web interface.

## Table of Contents
1. [Python Code Overview](#python-code-overview)
2. [HTML Code Overview](#html-code-overview)
3. [Functionality](#functionality)
4. [Setup Instructions](#setup-instructions)
5. [Usage Instructions](#usage-instructions)

## Python Code Overview

### Imports and Constants

```python
import socket
import network
import time
import ujson as json
import utime as time_lib
from machine import Pin, PWM
```
- **socket**: For network communication.
- **network**: To manage network connections.
- **time** and **utime**: For timing operations.
- **ujson**: For handling JSON data.
- **Pin**, **PWM**: For controlling GPIO pins and PWM signals.

### GPIO Pin Definitions
```python
# Pin numbers for various components
BUILT_IN_LED = 25
FLED = 20
BLED = 21
PWM_LM = 6
PWM_RM = 7
PWM_SC = 10
```

### Network Credentials
```python
SSID = b'ssid'
PWD = b'pwd'
```

### Class Definition: `RobotController`

#### Initialization and Setup
```python
class RobotController:
    def __init__(self):
        self.setup_pins()
        self.setup_servos()
        self.setup_network()
```
- **setup_pins()**: Initializes GPIO pins for LEDs.
- **setup_servos()**: Initializes PWM for servos.
- **setup_network()**: Sets up the network connection.

#### Pin Setup
```python
def setup_pins(self):
    self.built_in_led = Pin(BUILT_IN_LED, Pin.OUT)
    self.fled = Pin(FLED, Pin.OUT)
    self.bled = Pin(BLED, Pin.OUT)
```

#### Servo Setup
```python
def setup_servos(self):
    self.LeftMotor = PWM(Pin(PWM_LM))
    self.LeftMotor.freq(50)
    self.RightMotor = PWM(Pin(PWM_RM))
    self.RightMotor.freq(50)
    self.PanMotor = PWM(Pin(PWM_SC))
    self.PanMotor.freq(50)
```

#### Network Setup
```python
def setup_network(self):
    network.hostname("mypicow")
    self.wlan = network.WLAN(network.STA_IF)
    self.wlan.active(True)
```

### Robot Control Methods

#### Move Forward
```python
def move_forward(self, power, time):
    self.LeftMotor.duty_u16(7000)
    self.RightMotor.duty_u16(3000)
    time.sleep(time)
    self.LeftMotor.duty_u16(5000)
    self.RightMotor.duty_u16(5000)
```

#### Handle Emergency Stop
```python
def handle_emergency_stop(self):
    self.LeftMotor.duty_u16(0)
    self.RightMotor.duty_u16(0)
    self.PanMotor.duty_u16(0)
    self.blink_leds()
```

#### Blink LEDs
```python
def blink_leds(self):
    for _ in range(5):
        self.fled.value(not self.fled.value())
        self.bled.value(not self.bled.value())
        time.sleep(0.5)
```

#### Connect to WiFi
```python
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
```

### Server Request Handling

#### Serve Requests
```python
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
```

### Main Function
```python
def main():
    robot = RobotController()
    robot.connect_wifi()
    robot.serve_requests()

if __name__ == "__main__":
    main()
```

## HTML Code Overview

The HTML file creates a web interface with buttons to control the robot's LEDs and movement.

```html
<!DOCTYPE html>
<html>
<head>
    <title>Pi Pico Web Server</title>
</head>
<body>
    <h1>Pico W Web Server</h1>
    <h2>Controls</h2>
    <img src="https://images.pexels.com/photos/1779487/pexels-photo-1779487.jpeg?cs=srgb&dl=pexels-designecologist-1779487.jpg" width=320px height=213px>

    <form action="" method="get">
        <input type="submit" name="PRESS" value="FRONT_LED_ON" />
    </form>

    <form action="" method="get">
        <input type="submit" name="PRESS_1" value="FRONT_LED_OFF" />
    </form>

    <form action="" method="get">
        <input type="submit" name="PRESS_2" value="BACK_LED_ON" />
    </form>

    <form action="" method="get">
        <input type="submit" name="PRESS_3" value="BACK_LED_OFF" />
    </form>

    <form action="" method="get">
        <input type="submit" name="PRESS_4" value="MOVE" />
    </form>

    <form action="" method="get">
        <input type="submit" name="emergency_stop" value="Emergency Stop" />
    </form>

    <p>Lorem ipsum dolor sit amet</p>
</body>
</html>
```

## Functionality

1. **LED Control**: Turn the front and back LEDs on or off.
2. **Movement**: Move the robot forward.
3. **Emergency Stop**: Stop all movements and make the LEDs blink to indicate an emergency.

## Setup Instructions

1. **Hardware Setup**: Connect the LEDs and servos to the appropriate GPIO pins on the Raspberry Pi Pico W.
2. **Network Configuration**: Update the `SSID` and `PWD` variables with your WiFi network's credentials.
3. **File Setup**: Ensure both the Python script and the HTML file (`main.html`) are in the correct locations.

## Usage Instructions

1. **Run the Python Script**: Execute the Python script on the Raspberry Pi Pico W.
2. **Connect to the Web Interface**: Open a web browser and navigate to the IP address printed in the console after connecting to WiFi.
3. **Control the Robot**: Use the buttons on the web interface to control the LEDs, move the robot, and activate the emergency stop function.
