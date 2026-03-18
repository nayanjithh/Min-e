import time
import board
import busio
from PIL import Image, ImageDraw
import adafruit_ssd1306

from PIL import ImageFont
font = ImageFont.load_default()

i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)


def test():
    for _ in range(2):
        neutral()
        time.sleep(2)

        image = Image.open("./Emotions/Idle/Left.png").convert("1")
        image = image.resize((128, 64))
        oled.image(image)
        oled.show()
        time.sleep(2)

        image = Image.open("./Emotions/Idle/Bottom-left.png").convert("1")
        image = image.resize((128, 64))
        oled.image(image)
        oled.show()
        time.sleep(2)

        image = Image.open("./Emotions/Idle/Top-left.png").convert("1")
        image = image.resize((128, 64))
        oled.image(image)
        oled.show()
        time.sleep(2)

        image = Image.open("./Emotions/Idle/Right.png").convert("1")
        image = image.resize((128, 64))
        oled.image(image)
        oled.show()
        time.sleep(2)

        image = Image.open("./Emotions/Idle/Bottom-right.png").convert("1")
        image = image.resize((128, 64))
        oled.image(image)
        oled.show()
        time.sleep(2)

        image = Image.open("./Emotions/Idle/Top-right.png").convert("1")
        image = image.resize((128, 64))
        oled.image(image)
        oled.show()
        time.sleep(2)

        happy()
        time.sleep(2)

        sad()
        time.sleep(2)

        angry()
        time.sleep(2)

        blink()
        time.sleep(2)

        confused()
        time.sleep(2)

        love()
        time.sleep(2)

        image = Image.open("./Emotions/Head_or_Tails/Head.png").convert("1")
        image = image.resize((128, 64))
        oled.image(image)
        oled.show()
        time.sleep(2)

        image = Image.open("./Emotions/Head_or_Tails/Tail.png").convert("1")
        image = image.resize((128, 64))
        oled.image(image)
        oled.show()
        time.sleep(2)

def display(text):
    image = Image.new("1", (128, 64))
    draw = ImageDraw.Draw(image)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (128 - text_width) // 2
    y = (64 - text_height) // 2

    draw.text((x, y), text, font=font, fill=255)

    oled.image(image)
    oled.show()

def happy():
    image = Image.open("./Emotions/Happy/Happy.png").convert("1")
    image = image.resize((128, 64))
    oled.image(image)
    oled.show()

def neutral():
    image = Image.open("./Emotions/Idle/Normal.png").convert("1")
    image = image.resize((128, 64))
    oled.image(image)
    oled.show()

def sleep():
    pass

def angry():
    image = Image.open("./Emotions/Angry/Angry.png").convert("1")
    image = image.resize((128, 64))
    oled.image(image)
    oled.show()

def sad():
    image = Image.open("./Emotions/Sad/Sad.png").convert("1")
    image = image.resize((128, 64))
    oled.image(image)
    oled.show()

def love():
    image = Image.open("./Emotions/Love/Love.png").convert("1")
    image = image.resize((128, 64))
    oled.image(image)
    oled.show()

def confused():
    image = Image.open("./Emotions/Confused/Confused.png").convert("1")
    image = image.resize((128, 64))
    oled.image(image)
    oled.show()

def blink():
    image = Image.open("./Emotions/Blink/Blink.png").convert("1")
    image = image.resize((128, 64))
    oled.image(image)
    oled.show()
    time.sleep(0.02)
    neutral()
    

if __name__ == "__main__":
    try:
        test()
        display("Hi!, I am Mini...")
        #for _ in range(10):
         #   blink()
          #  time.sleep(5)

    except KeyboardInterrupt:
        print("Stopped")
        image = Image.open("./Emotions/Idle/Normal.png").convert("1")
        image = image.resize((128, 64))
        oled.image(image)
        oled.show()
