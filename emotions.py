import time
import oled
import random

def emotions(emotion):
    if emotion == "Happiness":
        oled.happy()
    elif emotion == "Neutral":
        oled.neutral()
    elif emotion == "Confused":
        oled.confused()
    elif emotion == "Sadness":
        oled.sad()
    elif emotion == "Anger":
        oled.angry()
    elif emotion == "Love":
        oled.love()
    elif emotion == "Blink":
        oled.blink()
    elif emotion == "idle":
        choice = random.randint(0,11)
        if choice == 6:
            emotions("Sadness")
        elif choice == 8:
            emotions("Happiness")

def test():
    oled.happy()
    time.sleep(2)

    oled.neutral()
    time.sleep(2)

    oled.confused()
    time.sleep(2)

    oled.sad()
    time.sleep(2)

    oled.angry()
    time.sleep(2)

    oled.love()
    time.sleep(2)

    oled.blink()
    time.sleep(2)

if __name__ == "__main__":
    test()
