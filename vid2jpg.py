'''
pip install opencv-python, alive-progress
'''
import cv2, sys, os, progress_cli
from alive_progress import alive_bar
from concurrent.futures import ThreadPoolExecutor


video_path = sys.argv[1]
vcap = cv2.VideoCapture(video_path)
folder_name = 'vid'
total_frames = int(vcap.get(cv2.CAP_PROP_FRAME_COUNT))


def extract_frame(start, stop, idx):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    count = start
    while count <= stop:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imwrite(f'{folder_name}/frame_{count:04d}.jpg', frame)
        count += 1
        progress_cli.copy_progress(idx, count, stop)
    cap.release()
    #print(f"Extracted {count} frames.")

def exctract_frame_cli():
    frame_count = 0
    with alive_bar(total_frames, spinner='classic') as bar:
        while True:
            ret, frame = vcap.read()
            if not ret:
                break
            frame_filename = f'{folder_name}/frame_{frame_count:04d}.jpg'
            cv2.imwrite(frame_filename, frame)
            frame_count += 1
            bar()
    print(f"Extracted {frame_count} frames.")


try:
    stem = os.path.basename(sys.argv[1].split('.')[0])
    os.makedirs(stem)
    folder_name = stem
except Exception as e:
    print('Using folder "vid"')
    os.makedirs(folder_name)


if len(sys.argv) > 2:
    print('Multi-thread')
    threads = int(sys.argv[2])
    extra = total_frames % threads
    num = total_frames // threads
    chopped = []
    # Split frames into equal chunks for each thread
    for r in range(0, threads):
        chopped.append((num*r, num*(r+1)-1))

    # Add remainder frames to last thread
    chopped[-1] = (chopped[-1][0], chopped[-1][1]+extra)
    progress_cli.clear_console()
    with ThreadPoolExecutor(max_workers=threads) as x:
        for i, c in enumerate(chopped):
            x.submit(extract_frame, c[0], c[1], i)
    progress_cli.clear_console()
else:
    print('Single-thread')
    exctract_frame_cli()

vcap.release()

