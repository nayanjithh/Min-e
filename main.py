#IMPORTS
import io, os, time, threading, asyncio, base64

import pygame
import speech_recognition as sr
import edge_tts
from groq import Groq

import cv2
import numpy as np
from picamera2 import Picamera2

import RPi.GPIO as GPIO
import requests

import bo_motor as bo
import servo
import wifi
import oled
import led

os.environ["PYTHONWARNINGS"] = "ignore"

# CONSTANTS
Name = "Mini"
QWEN_API_KEY = <QWEN_API_KEY>
GROQ_API_KEY = <GROQ_API_KEY>

client = Groq(api_key=<GROQ_API_KEY>)

#GPIO SETUP
FRONT = 4
LEFT  = 5
RIGHT = 6
BACK  = 16

GPIO.setmode(GPIO.BCM)
GPIO.setup(FRONT, GPIO.IN)
GPIO.setup(RIGHT, GPIO.IN)
GPIO.setup(BACK, GPIO.IN)
GPIO.setup(LEFT, GPIO.IN)

# CONFIG
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
BOX_WIDTH = 300
BOX_HEIGHT = 100
CONF_THRESHOLD = 0.6
VERTICAL_OFFSET = 100

MIN_FACE_AREA = 9000
MAX_FACE_AREA = 40000

# GLOBALS
recognizer = sr.Recognizer()
speaking = False
memory = []
respect = 100
stop_timer = 10
last_direction = "NONE"

pygame.mixer.init(frequency=24000)

sound_event = threading.Event()
track_event = threading.Event()

latest_frame = None
camera_running = True


#INITIALIZATION
bo.init()
servo.init()

#CAMARA
net = cv2.dnn.readNetFromCaffe(
    "deploy.prototxt",
    "res10_300x300_ssd_iter_140000.caffemodel"
)

net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

picam2 = Picamera2()
picam2.preview_configuration.main.size = (FRAME_WIDTH, FRAME_HEIGHT)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()

box_x1 = FRAME_WIDTH // 2 - BOX_WIDTH // 2
box_y1 = FRAME_HEIGHT // 2 - BOX_HEIGHT // 2 - VERTICAL_OFFSET
box_x2 = box_x1 + BOX_WIDTH
box_y2 = box_y1 + BOX_HEIGHT

def display(emotion):
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
    elif emotion in ["Love", "Excitement"]:
        oled.love()
    elif emotion == "Blink":
        oled.blink()
    else:
        oled.display(emotion)

def camera_loop():
    global latest_frame

    while camera_running:
        try:
            frame = picam2.capture_array()
            latest_frame = cv2.rotate(frame, cv2.ROTATE_180)
            time.sleep(0.03)
        except Exception as e:
            print("Camera error:", e)
            continue

def track_direction():
    global last_direction
    while sound_event.is_set():
        counts = {"FRONT": 0, "LEFT": 0, "RIGHT": 0, "BACK": 0}

        for _ in range(10):
            if GPIO.input(FRONT):
                counts["FRONT"] += 1
            if GPIO.input(LEFT):
                counts["LEFT"] += 1
            if GPIO.input(RIGHT):
                counts["RIGHT"] += 1
            if GPIO.input(BACK):
                counts["BACK"] += 1

            time.sleep(0.01)
        best = max(counts, key=counts.get)

        if counts[best] >= 2:
            last_direction = best

        time.sleep(0.05)

async def speak(text):
    global speaking
    communicate = edge_tts.Communicate(text, voice="en-US-GuyNeural")

    audio_bytes = b""

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]

    audio_file = io.BytesIO(audio_bytes)

    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        speaking = True
        await asyncio.sleep(0.05)
    speaking = False
    display("Neutral")


def TTS(text):
    asyncio.run(speak(text))

def capture():
    frame = latest_frame
    if frame is None:
        return False
    cv2.imwrite("view.jpg", frame)
    return True

def gpt_vision(prompt):
    if not capture():
        return "Camera not ready"
    display("processing")
    with open("view.jpg", "rb") as img:
        image_base64 = base64.b64encode(img.read()).decode()

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "qwen/qwen3.5-flash-02-23",
        "messages": [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": f"""
                        Your name is MINI.
                        You are a small humanoid robot powered by a Raspberry Pi 4.
                        You have:
                        - a camera for vision

                        Behavior:
                        - Respect level: {respect}%
                        - Sarcasm level: : {100 - respect}%
                        - Speak in ONE short sentence only.

                        When an image is provided:
                        1. First describe what you visually observe.
                        2. Then reason about what the object might be.
                        3. Then answer the user's question.

                        Speak like a friendly robot assistant.
                        Use simple sentences.

                        Format:
                        Just final answer

                        Do not mention AI or models.

                        Last chat:
                            {memory}
                        """}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        display("Neutral")
        result = response.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "I cannot see clearly.")
    except Exception as e:
        display("Sadness")
        return "I cannot see properly right now."
    
def chat_with_gpt(prompt):

    system_prompt = f"""
    Your name is MINI.

    You are a small humanoid robot powered by a Raspberry Pi 4.
    You have:
    - 4 servo motors for movement
    - an OLED display for emotions
    - a camera for vision

    Behavior:
    - Respect level: {respect}%
    - Sarcasm level: {100 - respect}%
    - Speak in ONE short sentence only.

    Emotion Rules:
    Start every response with an emotion in circular brackets.

    Allowed emotions:
    (Happiness), (Sadness), (Anger), (Neutral), (Confused), (Love)

    Example:
    (Happiness) Hello, I am feeling great today.

    Vision Rule (VERY IMPORTANT):
    If the user asks about appearance, objects, colors, surroundings, or anything that requires visual understanding (
        for example:
            "How do i look?"
            "what is this", 
            "what is in my hand", 
            "what am I holding", 
            "what do you see", 
            "what color is this", 
            or "look at this"
        ),
    respond ONLY with the exact string "__vision__".
    Do not include emotions, explanations, or any additional text when returning "__vision__".

    If the user says to turn on/off lights respond ONLY with the exact string "__lights__".
    Do not include emotions, explanations, or any additional text when returning "__lights__".

    Last chat:
        {memory}
    """

    try:
        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        emotion = "Neutral"
        response = chat.choices[0].message.content.strip()
    except Exception as e:
        emotion = "Confused"
        response = "Sorry, I am having trouble thinking right now."
    
    if "__vision__" in response:
        response = gpt_vision(prompt)
    elif "__lights__" in response:
        response = ToggleLights()
    elif response.startswith('('):
        parts = response.split(")", 1)
        emotion = parts[0][1:]
        response = parts[1].strip()
        
    if not response:
        response = "I did not understand that."

    display(emotion)
    memory.append(f"User: {prompt} \nMini: {response}\n")
    if len(memory) > 20:
        memory.pop(0)
    return response

def detect_face():
    frame = latest_frame
    if frame is None:
        return False

    blob = cv2.dnn.blobFromImage(
        frame,
        1.0,
        (300, 300),
        (104.0, 177.0, 123.0)
    )

    net.setInput(blob)
    detections = net.forward()

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        if confidence > CONF_THRESHOLD:
            return True

    return False

def activate_face_track():
    track_event.set()
    while track_event.is_set():
        frame = latest_frame
        if frame is None:
            continue
        h, w = frame.shape[:2]

        face_found = False

        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300),
                                     (104.0, 177.0, 123.0))
        net.setInput(blob)
        detections = net.forward()

        cv2.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), (255, 0, 0), 2)

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            if confidence > CONF_THRESHOLD:
                face_found = True

                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x1, y1, x2, y2) = box.astype("int")

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                face_center_x = (x1 + x2) // 2
                face_center_y = (y1 + y2) // 2
                cv2.circle(frame, (face_center_x, face_center_y), 5, (0, 0, 255), -1)

                direction = "STOP"

                if box_x1 < face_center_x < box_x2 and box_y1 < face_center_y < box_y2:
                    face_area = (x2 - x1) * (y2 - y1)
                    if face_area < MIN_FACE_AREA:
                        direction = "FORWARD"
                        bo.forward()
                        time.sleep(0.1)
                    elif face_area > MAX_FACE_AREA:
                        direction = "BACKWARD"
                        bo.backward()
                        time.sleep(0.1)
                elif face_center_x < box_x1:
                    direction = "LEFT"
                elif face_center_x > box_x2:
                    direction = "RIGHT"
                elif face_center_y < box_y1:
                    direction = "UP"
                else:
                    direction = "DOWN"

                if direction == "LEFT":
                    bo.left()
                elif direction == "RIGHT":
                    bo.right()
                elif direction == "UP":
                    servo.up()
                elif direction == "DOWN":
                    servo.down()
                else:
                    bo.stop()
                    servo.stop()
                break

        if not face_found:
            bo.stop()
            servo.stop()
        
        time.sleep(0.02)
        
def get_working_mic():
    mics = sr.Microphone.list_microphone_names()
    for i, name in enumerate(mics):
        try:
            mic = sr.Microphone(device_index=i)
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"✅ Using mic {i}")
            return mic
        except:
            continue
    raise Exception("❌ No working microphone found")

def change_respect(prompt):
    global respect
    if prompt.lower() in ["respect at 0 %", "respect at 0%"]:
        respect = 0
    elif prompt.lower() in ["respect at 25 %", "respect at 25%"]:
        respect = 25
    elif prompt.lower() in ["respect at 75 %", "respect at 75%"]:
        respect = 75
    elif prompt.lower() in ["respect at 100 %", "respect at 100%"]:
        respect = 100
    else:
        respect = 50
    response = f"Respect changed to {respect}%"
    display("Happiness")
    print(f"Chatbot: {response}")
    TTS(response)

def ToggleLights():
    light = led.lights()
    if not light:
         response = "Lights turned off"
         display("Happiness")
         print(f"Chatbot: {response}")
         TTS(response)
         return response
    else:
         response = "Lights turned on"
         display("Happiness")
         print(f"Chatbot: {response}")
         TTS(response)
         return response

def hearing_task(source):
    global stop_timer
    user_input = ""
    while True:
        try:
            if not wifi.connectivity():
                display("Sadness")
                print("wifi disconnected")
                TTS("Wifi disconnected")
                break
            if speaking:
                time.sleep(0.05)
                continue
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            user_input = recognizer.recognize_google(audio)
            print("You:", user_input)
            stop_timer = 10

            if user_input.lower() in ["stop", "thanks", "thank you"]:
                TTS("My pleasure")
                track_event.clear()
                break

            response = chat_with_gpt(user_input)

            if response == "__vision__":
                print("Checking camara")
            else:
                print("Mini:", response)
                TTS(response)

        except sr.WaitTimeoutError:
            print(".")
            display("Blink")
            stop_timer -= 1
            if stop_timer <= 0:
                break

        except sr.UnknownValueError:
            print("I didn't understand.")
            display("Confused")
            time.sleep(0.3)
            display("Neutral")
        
        except sr.RequestError:
            display("STT API unavailable")
            time.sleep(0.5)

        except KeyboardInterrupt:
            break

def start(source):
    global memory

    response = f"Hi, I am {Name}. Nice to meet you."
    print("Mini:", response)
    display("Neutral")
    TTS(response)

    sound_event.set()
    threading.Thread(target=track_direction, daemon=True).start()

    while True:
        print(f"Say 'Hey {Name}'")

        if not wifi.connectivity():
            display("Wifi not connected")
            time.sleep(1)
            continue
        else:
            try:
                if speaking:
                    time.sleep(0.05)
                    continue

                audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                user_input = recognizer.recognize_google(audio)
                print("You:", user_input)

                if user_input.lower() in ["hello", "hello hello", "hey mini", "hi mini", "mini"]:
                    sound_event.clear()
                    time.sleep(0.1)

                    print(f"➡️ Sound from {last_direction}")

                    for _ in range(8):
                        if detect_face():
                            bo.stop()
                            servo.stop()
                            response = "Yes, how can I help you?"
                            display("Happiness")
                            print("Mini:", response)
                            TTS(response)
                            display("Neutral")

                            t1 = threading.Thread(target=hearing_task, args=(source,))
                            t2 = threading.Thread(target=activate_face_track)

                            t1.start()
                            t2.start()

                            t1.join()
                            t2.join()
                            break
                        else:
                            print(f"turning {last_direction}")

                            if last_direction == "RIGHT":
                                bo.right()
                            elif last_direction == "LEFT":
                                bo.left()
                            elif last_direction == "BACK":
                                bo.turn_around()
                    bo.stop()
                    servo.stop()
                    sound_event.set()

            except sr.WaitTimeoutError:
                print(".")
                display("Blink")

            except sr.UnknownValueError:
                print("Didn't catch that.")
                display("Confused")
                time.sleep(0.3)
                display("Neutral")
            
            except sr.RequestError:
                display("STT API unavailable")
                time.sleep(0.5)

            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    while not wifi.connectivity():
            display("Wifi not connected")
            time.sleep(1)

    mic = get_working_mic()
    with mic as source:
        print("Calibrating microphone...")
        recognizer.adjust_for_ambient_noise(source, duration=3)
        threading.Thread(target=camera_loop, daemon=True).start()
        print("Ready")
        start(source)
    
    camera_running = False 
    time.sleep(0.1)
    picam2.stop()
    sound_event.clear()
    track_event.clear()