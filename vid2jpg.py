import cv2, sys, os
from alive_progress import alive_bar

video_path = sys.argv[1]
cap = cv2.VideoCapture(video_path)

folder_name = ''

frame_count = 0
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

try:
    os.makedirs(sys.argv[1])
    folder_name = sys.argv[1]
except Exception as e:
    print(e)
    os.makedirs('vid')
    folder_name = 'vid'

with alive_bar(total_frames, spinner='classic') as bar:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_filename = f'{folder_name}/frame_{frame_count:04d}.jpg'
        cv2.imwrite(frame_filename, frame)
        frame_count += 1
        bar()
        #print(frame_count, end='\r')

cap.release()
print(f"Extracted {frame_count} frames.")
