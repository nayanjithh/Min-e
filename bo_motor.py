import RPi.GPIO as GPIO
import time
import random

import us_sensor as us

IN1 = 17
IN2 = 27
IN3 = 22
IN4 = 23
ENA = 12
ENB = 13

SPEED = 90

def sensor_move():
    num = random.choice([1, 2, 3, 4])
    if num == 1:
        forward()
        for _ in range(200):
            if us.object_detection():
                print("Object detected")
                stop()
                time.sleep(1)
                backward()
                time.sleep(0.1)
                stop()
                right()
                time.sleep(0.2)
                stop()
                break
    elif num == 2:
        right()
        time.sleep(0.4)
    elif num == 3:
        left()
        time.sleep(0.4)
    else:
        time.sleep(2)
    stop()

def forward():
    print("Forward")
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    time.sleep(0.3)
    stop()

def backward():
    print("Backward")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    time.sleep(0.3)
    stop()

def left():
    print("Left")
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    time.sleep(0.3)
    stop()

def right():
    print("Right")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    time.sleep(0.3)
    stop()

def turn_around():
    print("Turning 180")
    right()
    time.sleep(0.5)
    stop()

def stop():
    #print("Stop")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)

def init():
    global pwmA, pwmB

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    pins = [IN1, IN2, IN3, IN4, ENA, ENB]
    for p in pins:
        GPIO.setup(p, GPIO.OUT)

    pwmA = GPIO.PWM(ENA, 1000)
    pwmB = GPIO.PWM(ENB, 1000)

    pwmA.start(SPEED)
    pwmB.start(SPEED)

def main():
    init()

    try:
        while True:
            forward()
            time.sleep(1)

            stop()
            time.sleep(1)

            right()
            time.sleep(1)

            left()
            time.sleep(1)

            backward()
            time.sleep(1)

            stop()
            time.sleep(2)

    except KeyboardInterrupt:
        print("Stopped by user")

    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    #main()
    init()
    while True:
        sensor_move()
        time.sleep(1)

