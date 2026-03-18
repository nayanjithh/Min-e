import io
import pygame
import speech_recognition as sr
import asyncio
import edge_tts
from groq import Groq
import time
import os

import cv2

os.environ["PYTHONWARNINGS"] = "ignore"

import threading

import numpy as np
from picamera2 import Picamera2

import bo_motor as bo
import servo
import wifi

import RPi.GPIO as GPIO
import time
import speech_recognition as sr
import os
import threading

# -------- GPIO SETUP --------
FRONT = 4
LEFT  = 5
RIGHT = 6
BACK  = 16

GPIO.setmode(GPIO.BCM)
GPIO.setup(FRONT, GPIO.IN)
GPIO.setup(RIGHT, GPIO.IN)
GPIO.setup(BACK, GPIO.IN)
GPIO.setup(LEFT, GPIO.IN)

recognizer = sr.Recognizer()

# ------------------------------
# CONFIG: Change these as needed
# ------------------------------
FRAME_WIDTH = 640   # Camera width
FRAME_HEIGHT = 480  # Camera height
BOX_WIDTH = 300
BOX_HEIGHT = 100
CONF_THRESHOLD = 0.6 # Confidence threshold for DNN
VERTICAL_OFFSET = 100   # move box up (increase value to move more up)
last_direction = "STOP"

MIN_FACE_AREA = 9000   # too far -> move forward
MAX_FACE_AREA = 40000   # too close -> move backward

bo.init()
servo.init()

# ------------------------------
# Load DNN Face Detector Model
# ------------------------------
net = cv2.dnn.readNetFromCaffe(
    "deploy.prototxt",
    "res10_300x300_ssd_iter_140000.caffemodel"
)


# Optional: enforce CPU usage for DNN
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

# ------------------------------
# Initialize Raspberry Pi Camera
# ------------------------------
picam2 = Picamera2()
picam2.preview_configuration.main.size = (FRAME_WIDTH, FRAME_HEIGHT)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()

# ------------------------------
# Calculate center square coordinates
# ------------------------------
box_x1 = FRAME_WIDTH // 2 - BOX_WIDTH // 2
box_y1 = FRAME_HEIGHT // 2 - BOX_HEIGHT // 2 - VERTICAL_OFFSET
box_x2 = box_x1 + BOX_WIDTH
box_y2 = box_y1 + BOX_HEIGHT

import requests
import base64

import oled
import led

API_KEY = <API_KEY>

Name = "Mini"
Track = False
speaking = False

memory = []
respect = 100
stop_timer = 10
last_direction = "NONE"
sound_dir = False

client = Groq(api_key=<API_KEY>)

recognizer = sr.Recognizer()

pygame.mixer.init(frequency=24000)

def track_direction():
    global last_direction, sound_dir

    while sound_dir:
        counts = {"FRONT": 0, "LEFT": 0, "RIGHT": 0, "BACK": 0}

        # 🔥 sample 10 times
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

        # ✅ pick strongest signal
        best = max(counts, key=counts.get)

        # ❗ ignore weak signals
        if counts[best] >= 2:   # threshold
            last_direction = best

        time.sleep(0.05)
        
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

def display(emotion):
    #print(f"[Emotion]: {emotion}")
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
    else:
         response = "Lights turned on"
         display("Happiness")
         print(f"Chatbot: {response}")
         TTS(response)

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
    #print("speaking")

def capture():
    display("camera")

    time.sleep(0.5)

    frame = picam2.capture_array()
    
    frame = cv2.rotate(frame, cv2.ROTATE_180)

    cv2.imwrite("view.jpg", frame)

    print("Image saved as view.jpg")

def gpt_vision(prompt):
    capture()
    display("processing")
    with open("view.jpg", "rb") as img:
        image_base64 = base64.b64encode(img.read()).decode()

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
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

    response = requests.post(url, headers=headers, json=data)
    display("Neutral")
    return response.json()["choices"][0]["message"]["content"]


# -----------------------
# LLM RESPONSE
# -----------------------
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

    chat = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    emotion = "Neutral"
    response = chat.choices[0].message.content.strip()
    
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
    return response
    
def activate_face_track():
    global Track
    while Track:
        frame = picam2.capture_array()
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        h, w = frame.shape[:2]

        face_found = False   # NEW: track if a face is detected

        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300),
                                     (104.0, 177.0, 123.0))
        net.setInput(blob)
        detections = net.forward()

        cv2.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), (255, 0, 0), 2)

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            if confidence > CONF_THRESHOLD:
                face_found = True   # FACE DETECTED

                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x1, y1, x2, y2) = box.astype("int")

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                face_area = (x2 - x1) * (y2 - y1)

                face_center_x = (x1 + x2) // 2
                face_center_y = (y1 + y2) // 2
                cv2.circle(frame, (face_center_x, face_center_y), 5, (0, 0, 255), -1)

                if box_x1 < face_center_x < box_x2 and box_y1 < face_center_y < box_y2:
                    direction = "MIDDLE"
                    face_area = (x2 - x1) * (y2 - y1)
                    if face_area < MIN_FACE_AREA:
                        direction = "FORWARD"
                        bo.forward()
                        time.sleep(0.5)
                    elif face_area > MAX_FACE_AREA:
                        direction = "BACKWARD"
                        bo.backward()
                        time.sleep(0.5)
                elif face_center_x < box_x1:
                    direction = "LEFT"
                elif face_center_x > box_x2:
                    direction = "RIGHT"
                elif face_center_y < box_y1:
                    direction = "UP"
                else:
                    direction = "DOWN"

                #print(direction)

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
            #print("NO FACE")
            bo.stop()
            servo.stop()
            
def detect_face():
    frame = picam2.capture_array()
    frame = cv2.rotate(frame, cv2.ROTATE_180)

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
            return True   # Face detected

    return False   # No face

def hearing_task(source):
    global stop_timer, Track
    while True:
        try:
            if not wifi.connectivity():
                display("Sadness")
                print("wifi disconnected")
                TTS("Wifi disconnected")
                break
            if not speaking:
                audio = recognizer.listen(source, timeout=5)
                user_input = recognizer.recognize_google(audio)
                print("You:", user_input)
                stop_timer = 10

            if user_input.lower() in ["stop", "thanks", "thank you"]:
                TTS("My pleasure")
                Track = False
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

        except KeyboardInterrupt:
            break

def start(source):
    global memory, Track, sound_dir

    response = f"Hi, I am {Name}. Nice to meet you."
    print("Mini:", response)
    display("Neutral")
    TTS(response)

    sound_dir = True
    threading.Thread(target=track_direction, daemon=True).start()

    while True:
        print(f"Say 'Hey {Name}'")

        if not wifi.connectivity():
            display("Wifi not connected")
            continue
        else:
            try:
                if not speaking:
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                    user_input = recognizer.recognize_google(audio)
                    print("You:", user_input)

                if user_input.lower() in ["hello", "hello hello", "hey mini", "hi mini", "mini"]:
                    sound_dir = False
                    time.sleep(0.1)

                    print(f"➡️ Sound from {last_direction}")

                    for _ in range(8):
                        if detect_face():
                            response = "Yes, how can I help you?"
                            display("Happiness")
                            print("Mini:", response)

                            Track = True
                            TTS(response)
                            display("Neutral")

                            t1 = threading.Thread(target=hearing_task, args=(source,))
                            t2 = threading.Thread(target=activate_face_track)

                            t1.start()
                            t2.start()

                            t1.join()
                            t2.join()

                            sound_dir = True
                            threading.Thread(target=track_direction, daemon=True).start()

                            if not Track:
                                break
                        else:
                            print(f"turning {last_direction}")

                            if last_direction == "RIGHT":
                                bo.right()
                            elif last_direction == "LEFT":
                                bo.left()
                            elif last_direction == "BACK":
                                bo.turn_around()

            except sr.WaitTimeoutError:
                print(".")
                display("Blink")

            except sr.UnknownValueError:
                print("Didn't catch that.")
                display("Confused")
                time.sleep(0.3)
                display("Neutral")

            except KeyboardInterrupt:
                break
# -----------------------
# MAIN
# -----------------------
if __name__ == "__main__":
    while not wifi.connectivity():
            display("Wifi not connected")
    mic = get_working_mic()
    with mic as source:
        print("Calibrating microphone...")
        recognizer.adjust_for_ambient_noise(source, duration=3)
        print("Ready")
        start(source)

    picam2.stop()
