import RPi.GPIO as GPIO
import time

SERVO_PIN = 25

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0)

angle = 45   # starting position

def set_angle(a):
    duty = 2 + (a / 18)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.2)
    pwm.ChangeDutyCycle(0)


def up():
    global angle
    if angle < 90:
        angle += 15
        angle = min(angle, 120)
        set_angle(angle)


def down():
    global angle
    if angle > 0: 
        angle -= 10
        angle = max(angle, 10)
        set_angle(angle)


def stop():
    pwm.ChangeDutyCycle(0)


def cleanup():
    pwm.stop()
    GPIO.cleanup()

def init():
    set_angle(angle)


if __name__ == "__main__":
    set_angle(0)
    time.sleep(2)
    set_angle(65)
    time.sleep(2)
    stop()
    cleanup()
