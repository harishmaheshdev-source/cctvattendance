import cv2
import face_recognition
import os
import csv
from datetime import datetime
import requests
import serial

pico = serial.Serial('COM6', 9600)  # ⚠️ change COM3 to your port
last_state = None

print("Starting system...")

# =========================
# CSV SETUP
# =========================
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "attendance.csv")

if not os.path.exists(csv_path):
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Date", "Time"])

# Prevent duplicate entries
marked_today = set()

# =========================
# LOAD DATASET
# =========================
known_encodings = []
known_names = []

dataset_path = r"C:\Users\jsish\Downloads\Programming\CCTV based attendace\auto_attendance\dataset"

for person_name in os.listdir(dataset_path):
    person_folder = os.path.join(dataset_path, person_name)

    if not os.path.isdir(person_folder):
        continue

    print("Loading:", person_name)

    for image_name in os.listdir(person_folder):
        image_path = os.path.join(person_folder, image_name)

        if not (image_name.endswith(".jpg") or image_name.endswith(".png")):
            continue

        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)

        if len(encodings) > 0:
            known_encodings.append(encodings[0])
            known_names.append(person_name)

print("Dataset loaded!")
print("Total faces:", len(known_encodings))

# =========================
# START CAMERA
# =========================
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    faces = face_recognition.face_locations(rgb_frame)
    encodings = face_recognition.face_encodings(rgb_frame, faces)

    print("Faces detected:", len(faces))

    for face_encoding, face_location in zip(encodings, faces):
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        name = "Unknown"

        if True in matches:
            match_index = matches.index(True)
            name = known_names[match_index]

            # =========================
            # ATTENDANCE LOGGING
            # =========================
            if name not in marked_today:
                now = datetime.now()
                date = now.strftime("%Y-%m-%d")
                time = now.strftime("%H:%M:%S")

                with open(csv_path, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([name, date, time])

                marked_today.add(name)
                print(f"Attendance marked for {name}")
                try:
                    requests.post("http://127.0.0.1:5000/mark", json={
                        "name": name,
                        "date": date,
                        "time": time
                    })
                except:
                    print("Server not running")
        # 🔥 LED CONTROL (ADD THIS HERE)
        current_state = "UNKNOWN" if name == "Unknown" else "KNOWN"

        if current_state != last_state:
            if current_state == "UNKNOWN":
                pico.write(b"BLINK\n")
            else:
                pico.write(b"OFF\n")

            last_state = current_state
            
        # Draw box and name
        top, right, bottom, left = face_location

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow("Attendance System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()