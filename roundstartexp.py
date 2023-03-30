import cv2
import pytesseract
from pytesseract import Output
import time
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def process_video(video_path, output_path):
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_duration = time.strftime(
        "%H:%M:%S", time.gmtime(total_frames // fps))

    with open(output_path, "w") as output_file:
        for i in range(0, total_frames, fps * 3):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            roi = frame[15:15+197, 622:622+666]
            if ret:

                # Original ROI
                text_original = pytesseract.image_to_string(
                    roi, config="--psm 6")
                # adjust the image a bit for certain backgrounds
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                _, thresholded_roi = cv2.threshold(
                    gray_roi, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
                # parse text from the adjusted image
                text_thresholded = pytesseract.image_to_string(
                    thresholded_roi, config="--psm 6")
                # combine the strings retrieved from both the images
                text = f"{text_original} {text_thresholded}"
                # Keep only letters and whitespace
                text = re.sub(r'[^a-zA-Z\s]', '', text)
                text = text.strip()

                if text:
                    time_in_video = time.strftime(
                        "%H:%M:%S", time.gmtime(i // fps))
                    output_file.write(f"{time_in_video} \"{text}\"\n")

            # Print progress
            progress = time.strftime("%H:%M:%S", time.gmtime(i // fps))
            print(f"Scanned progress: {progress} / {total_duration}", end="\r")

    cap.release()
    print()


def main():
    video_path = "scrim.mp4"
    output_path = "output/log.txt"
    process_video(video_path, output_path)


if __name__ == "__main__":
    main()


# Player names scan
'''
nameplates = [
    (44, 113),
    (150, 113),
    (256, 113),
    (362, 113),
    (468, 113),
    (1356, 113),
    (1462, 113),
    (1568, 113),
    (1674, 113),
    (1780, 113)
]

player_names = []

# Apply OCR to the ROI

for i, coords in enumerate(nameplates):
    x, y = coords[0], coords[1]
    h, w = 25, 100
    roi = image[y:y+h, x:x+w]
    text = pytesseract.image_to_string(roi)
    player_names.append(text)

print(player_names)
'''
