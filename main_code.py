import RPi.GPIO as gpio
from gtts import gTTS
import pytesseract as pya
import face_recognition
from picamera2 import Picamera2
import os
import cv2
import time
import threading
import numpy as np
import serial
from flask import *


app=Flask(__name__)



picam = Picamera2()
picam.preview_configuration.main.size = (480, 480)
picam.preview_configuration.main.format = "RGB888"
picam.preview_configuration.main.align()
picam.configure("preview")
picam.start()


s="no"

help_btn = 16
obj_btn = 20
ocr_btn = 21
face_btn = 26
GPIO_TRIGGER = 17                  
GPIO_ECHO = 18


flag1=0
flag2=0
flag3=0
flag4=0

ser = serial.Serial(port='/dev/ttyS0', baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)


classesFile = '/home/pi/coco.names'
classNames = []
with open(classesFile, 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')

modelconfig = '/home/pi/yolov3tiny.cfg'
modelweight = '/home/pi/yolov3tiny.weights'
net = cv2.dnn.readNetFromDarknet(modelconfig, modelweight)

known_face_encodings = []
known_face_names = []


def load_known_faces():
    voter_image_dir = r'/home/pi/images'
    for image_filename in os.listdir(voter_image_dir):
        voter_name = os.path.splitext(image_filename)[0]
        image_path = os.path.join(voter_image_dir, image_filename)
        voter_image = face_recognition.load_image_file(image_path)
        voter_face_encoding = face_recognition.face_encodings(voter_image)[0]  # Assuming one face per image
        known_face_encodings.append(voter_face_encoding)
        known_face_names.append(voter_name)
        print("face loaded")
load_known_faces()

def face_check():
    print("System is going to check face authentication")
    print("Please look at the camera")

    # Initialize system camera (use 0 for default camera)
    camera = cv2.VideoCapture(0)
    
    face_flag=0
    while face_flag==0:
        try:
            # Display camera preview for 5 seconds
            start_time = time.time()
            while time.time() - start_time < 5:
                frame = picam.capture_array()
                cv2.imshow('Live Detection', frame)
                cv2.waitKey(1)
            # Save the captured frame as an image
            cv2.imwrite("captured_image.jpg", frame)
            # Close all windows
            cv2.destroyAllWindows()
            # Read the saved image
            frame = cv2.imread("captured_image.jpg")
            

            # Find all face locations and face encodings in the current frame
            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Compare face_encoding with known_face_encodings
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)

                name = "Unknown"

                # Check if there's a match
                if True in matches:
                    match_index = matches.index(True)
                    name = known_face_names[match_index]
                    if name:
                        print(name)
                        speak(name)
                        face_flag=1
                else:
                    print(name)
                    speak(name)
                    face_flag=1
        except Exception as e:
            print(e)
    
    
                        
def main():
    global s
    global flag1,flag2,flag3,flag4
    gpio.setwarnings(False)
    gpio.setmode(gpio.BCM)
    gpio.setup(face_btn, gpio.IN)
    gpio.setup(ocr_btn, gpio.IN)
    gpio.setup(obj_btn, gpio.IN)
    gpio.setup(help_btn, gpio.IN)
    gpio.setup(GPIO_TRIGGER, gpio.OUT)
    gpio.setup(GPIO_ECHO, gpio.IN)
    threading.Thread(target=dist).start()
    
    speak("Welcome to the Smart Assistive System for the Blind")
    print("Welcome to the Smart Assistive System for the Blind")
    while True:
        global s
        help_val = gpio.input(help_btn)
        sign_val = gpio.input(obj_btn)
        ocr_val = gpio.input(ocr_btn)
        face_val = gpio.input(face_btn)

        if ocr_val == 0:
            flag1 = 1
        if ocr_val == 1 and flag1 == 1:
            flag1 = 0
            print("System is going to read text")
            speak("System is going to read text")
            readText()

        if sign_val == 0:
            flag2 = 1
        if sign_val == 1 and flag2 == 1:
            flag2 = 0
            detect()

        if help_val == 0:
            flag3 = 1
        if help_val == 1 and flag3 == 1:
            flag3 = 0
            ser.write('A'.encode())
            print("emergency")
            time.sleep(1)

        if face_val == 0:
            flag4 = 1
        if face_val == 1 and flag4 == 1:
            flag4 = 0
            print("System is going to check face")
            speak("System is going to check face")
            face_check()
            



def dist():
    while True:
        gpio.output(GPIO_TRIGGER, False)
        time.sleep(0.0001)
        gpio.output(GPIO_TRIGGER, True)
        time.sleep(0.0001)
        gpio.output(GPIO_TRIGGER, False)

        start_time = time.time()
        stop_time = time.time()

        while gpio.input(GPIO_ECHO) == 0:
            start_time = time.time()

        while gpio.input(GPIO_ECHO) == 1:
            stop_time = time.time()

        time_elapsed = stop_time - start_time
        distance = (time_elapsed * 34300) / 2
        print(distance)
        if distance<=20:
            speak("object infront of you")
            
def readText():
    try:
        print("System is reading your image. Please wait.")
        speak("System is reading your image. Please wait.")
        caps = cv2.VideoCapture(0)
        ocr_flag = 0
        while ocr_flag == 0:
            # Display camera preview for 5 seconds
            start_time = time.time()
            while time.time() - start_time < 5:
                frame = picam.capture_array()
                cv2.imshow('Live Detection', frame)
                cv2.waitKey(1)
            # Save the captured frame as an image
            cv2.imwrite("captured_image.jpg", frame)
            # Close all windows
            cv2.destroyAllWindows()
            frame = cv2.imread("captured_image.jpg")
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.bilateralFilter(gray, 11, 17, 17)
            text = pya.image_to_string(gray, config='')
            if text:
                print(text)
                speak(text)
                ocr_flag=1
    except Exception as e:
        print("Warning:", e)
        caps.release()
        cv2.destroyAllWindows()

def readImg():
    try:
        print("System is reading your image. Please wait.")
        speak("System is reading your image. Please wait.")
        caps = cv2.VideoCapture(0)
        img_flag = 0
        while img_flag == 0:
            # Display camera preview for 5 seconds
            start_time = time.time()
            while time.time() - start_time < 5:
                frame = picam.capture_array()
                cv2.imshow('Live Detection', frame)
                cv2.waitKey(1)
            # Save the captured frame as an image
            cv2.imwrite("captured.jpg", frame)
            # Close all windows
            cv2.destroyAllWindows()
            img = Image.open("captured.jpg")
            inputs = processor(img, return_tensors="pt")
            out = model.generate(**inputs)
            caption = processor.decode(out[0], skip_special_tokens=True)
            print(caption)
            if caption:
                print(caption)
                speak(caption)
                img_flag=1
    except Exception as e:
        print("Warning:", e)
        caps.release()
        cv2.destroyAllWindows()


def speak(text):
    myobj = gTTS(text=text, lang='en', slow=False)
    myobj.save("/home/pi/speech.mp3")
    os.system("mpg321 /home/pi/speech.mp3")


def detect():
    cap = cv2.VideoCapture(0)
    obj_flag = 0
    while obj_flag == 0:
        # Display camera preview for 5 seconds
        start_time = time.time()
        while time.time() - start_time < 5:
            img = picam.capture_array()
            cv2.imshow('Live Detection', img)
            cv2.waitKey(1)
        # Save the captured frame as an image
        cv2.imwrite("captured_image.jpg", img)
        # Close all windows
        cv2.destroyAllWindows()
        img = cv2.imread("captured_image.jpg")
        blob = cv2.dnn.blobFromImage(img, 1/255, (320, 320), [0, 0, 0], 1, crop=False)
        net.setInput(blob)
        layerNames = net.getLayerNames()
        a = net.getUnconnectedOutLayers()
        outputNames = [layerNames[i - 1] for i in net.getUnconnectedOutLayers()]
        outputs = net.forward(outputNames)
        h, w, c = img.shape
        bbox = []
        classids = []
        conf = []
        for output in outputs:
            for det in output:
                score = det[5:]
                classid = np.argmax(score)
                confidence = score[classid]
                if confidence > 0.4:
                    wd, ht = int(det[2] * w), int(det[3] * h)
                    x, y = int((det[0] * w) - wd / 2), int((det[1] * h) - ht / 2)
                    bbox.append([x, y, wd, ht])
                    classids.append(classid)
                    conf.append(float(confidence))
        indices = cv2.dnn.NMSBoxes(bbox, conf, 0.5, 0.3)
        for i in indices:
            i = i
            box = bbox[i]
            x, y, w, h = box[0], box[1], box[2], box[3]
            res=classNames[classids[i]]
            print(res)
            speak(res)
            obj_flag = 1

    
        

if __name__ == "__main__":
    main()
