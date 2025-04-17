import pickle
import cv2
import os
from datetime import datetime
import face_recognition
import numpy as np
import cvzone
from supabase import create_client

# Initialize Supabase
url = "https://cgfxkephzkmrijduhtua.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNnZnhrZXBoemttcmlqZHVodHVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ4NDIwMjAsImV4cCI6MjA2MDQxODAyMH0.VhuRuWRCQzlvBc1zr86k3B0quSq2xT5uBDNS8X3hNOI"
supabase = create_client(url, key)

# Camera setup
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # Width
cap.set(4, 480)  # Height

# Load background and modes
imgBackground = cv2.imread('Resources/background.png')
folderModePath = 'Resources/modes'
imgModeList = [cv2.imread(os.path.join(folderModePath, path)) for path in os.listdir(folderModePath)]

# Load face encodings
print("Loading Encode file...")
with open("EncodeFile.p", 'rb') as file:
    encodeListKnown, faceIds = pickle.load(file)
print("Encode file loaded")

# State variables
modeType = 0  # 0: default, 1: loading, 2: info display, 3: already marked
counter = 0
id = -1
imgUser = []

# Main loop
while True:
    success, img = cap.read()

    # Resize and convert image for face detection
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    # Detect faces
    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    # Update background
    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

    if faceCurFrame:
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                # Scale face location back to original size
                y1, x2, y2, x1 = [coord * 4 for coord in faceLoc]
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                id = faceIds[matchIndex]

                if counter == 0:
                    counter = 1
                    modeType = 1  # Switch to loading mode

    if counter != 0:
        if counter == 1:
            # Fetch user data from Supabase
            response = supabase.table("Users").select("*").eq("id", id).execute()
            userInfo = response.data[0] if response.data else None

            if userInfo:
                # Load user image
                try:
                    img_data = supabase.storage.from_("users-images").download(f"{id}.png")
                    img_np = np.frombuffer(img_data, np.uint8)
                    imgUser = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
                    if imgUser is None:
                        raise ValueError("Failed to decode image")
                except Exception as e:
                    print(f"Error loading user image: {e}")
                    imgUser = np.zeros((216, 216, 3), dtype=np.uint8)  # Black placeholder

                # Check attendance timing
                last_attendance = datetime.strptime(
                    userInfo['last_attendance_time'].replace('T', ' '),
                    "%Y-%m-%d %H:%M:%S"
                )
                secondsElapsed = (datetime.now() - last_attendance).total_seconds()

                if secondsElapsed > 30:  # 24-hour cooldown
                    # Update attendance
                    supabase.table("Users").update({
                        'total_attendance': userInfo['total_attendance'] + 1,
                        'last_attendance_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }).eq("id", id).execute()
                else:
                    modeType = 3  # Already marked mode
                    counter = 1  # Start counter for message display

        # Mode handling
        if modeType == 3:  # Already marked mode
            if counter >= 50:  # ~2.5 second display
                counter = 0
                modeType = 0
            else:
                counter += 1
                # Display "Already Marked" message
                cvzone.putTextRect(imgBackground, "Attendance Already Marked",
                                   (275, 400), scale=2, thickness=3)

        elif modeType != 0:  # Normal display mode
            if 30 < counter < 80:  # Show info display
                modeType = 2

            if counter <= 80 and userInfo and imgUser is not None:
                # Display user info
                cv2.putText(imgBackground, str(userInfo['total_attendance']), (861, 125),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                cv2.putText(imgBackground, str(userInfo['major']), (1006, 550),
                            cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(imgBackground, str(id), (1006, 493),
                            cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(imgBackground, str(userInfo['standing']), (910, 625),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                cv2.putText(imgBackground, str(userInfo['year']), (1025, 625),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                cv2.putText(imgBackground, str(userInfo['starting_year']), (1125, 625),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                # Center the name text
                (w, h), _ = cv2.getTextSize(userInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                offset = (414 - w) // 2
                cv2.putText(imgBackground, userInfo['name'], (808 + offset, 445),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                # Display user image
                imgBackground[175:175 + 216, 909:909 + 216] = imgUser

            counter += 1
            if counter >= 100:  # ~5 second display
                counter = 0
                modeType = 0
                userInfo = []
                imgUser = []
    else:
        modeType = 0
        counter = 0

    # Display the result
    cv2.imshow("Face Attendance", imgBackground)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()