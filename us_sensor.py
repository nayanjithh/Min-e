import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)

TRIG = 20
ECHO = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

GPIO.output(TRIG, False)
time.sleep(1)


def get_distance():

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    pulse_start = 0
    pulse_end = 0

    timeout = time.time()

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start - timeout > 0.02:
            return None

    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end - timeout > 0.02:
            return None

    duration = pulse_end - pulse_start
    distance = duration * 17150

    return distance

def object_detection():
    readings = []
    for _ in range(3):
        d = get_distance()
        if d is not None:
            readings.append(d)
        time.sleep(0.01)

    readings.sort()
    distance = readings[len(readings)//2]   # median

    distance_cm = round(distance * 100, 2)

    print("Distance:", distance_cm)

    #if distance_cm < 500:
    #    print("object in front")
    #elif distance_cm > 7000:
    #    print("hole")
    #else:
    #    print("floor")
    if distance_cm < 700:
        return 0
    elif distance_cm > 20000 and distance_cm < 3041227021765107.5:
        return 0
    else:
        return 1
        
    
if __name__ == "__main__":
    while object_detection():
        print("forward")
    print("stop")
