import cv2
import face_recognition
import pickle
import os
from supabase import create_client

# Initialize Supabase
url = "https://cgfxkephzkmrijduhtua.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNnZnhrZXBoemttcmlqZHVodHVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ4NDIwMjAsImV4cCI6MjA2MDQxODAyMH0.VhuRuWRCQzlvBc1zr86k3B0quSq2xT5uBDNS8X3hNOI"
supabase = create_client(url, key)

# Image processing
folderPath = 'Images'
pathList = os.listdir(folderPath)
imgList = []
faceIds = []

for path in pathList:
    try:
        # Load image
        img_path = os.path.join(folderPath, path)
        img = cv2.imread(img_path)
        if img is None:
            print(f"Failed to load {path}")
            continue

        imgList.append(img)
        student_id = os.path.splitext(path)[0]
        faceIds.append(student_id)

        # Upload to Supabase Storage (corrected version)
        with open(img_path, 'rb') as f:
            supabase.storage.from_("users-images").upload(
                file=f.read(),
                path=path
            )
        print(f"Uploaded {path}")

    except Exception as e:
        print(f"Error processing {path}: {str(e)}")


# Face encoding with error handling
def findEncodings(imagesList):
    encodeList = []
    for i, img in enumerate(imagesList):
        try:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encodes = face_recognition.face_encodings(img_rgb)
            if len(encodes) > 0:
                encodeList.append(encodes[0])
            else:
                print(f"No face found in image {i}")
        except Exception as e:
            print(f"Error encoding image {i}: {str(e)}")
    return encodeList


print("Encoding started...")
encodeListKnown = findEncodings(imgList)
encodeListKnownWithIds = [encodeListKnown, faceIds]

# Save encodings
with open("EncodeFile.p", 'wb') as file:
    pickle.dump(encodeListKnownWithIds, file)
print(f"Encodings saved for {len(encodeListKnown)} faces")

with open("student_mapping.txt", 'w') as f:
    for student_id in faceIds:
        f.write(f"{student_id}\n")
print("Fichier de mapping créé")