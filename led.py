import RPi.GPIO as GPIO
import time

LED_PIN = 26

GPIO.setmode(GPIO.BCM)

def lights():
    GPIO.setup(LED_PIN, GPIO.OUT)
    led_status = GPIO.input(LED_PIN)
    if led_status == GPIO.HIGH:
        GPIO.output(LED_PIN, GPIO.LOW)
        return 0
    else:
        GPIO.output(LED_PIN, GPIO.HIGH)
        return 1

if __name__ == "__main__":
    try:
        while True:
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopped by user")

    finally:
        GPIO.cleanup()
