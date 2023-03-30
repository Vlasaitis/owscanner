import numpy as np
from typing import Tuple
from exporter import seconds_to_timestamp
# from config import fps, total_duration, top_bar_interval_num, kf_interval_num
from config import top_bar_interval_num, kf_interval_num
import time
import cv2


def instantiate_video_variables(video):
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(video.get(cv2.CAP_PROP_FPS))
    total_duration = int(total_frames / fps)
    top_bar_interval = top_bar_interval_num * fps
    kf_interval = kf_interval_num * fps

    return total_frames, fps, total_duration, top_bar_interval, kf_interval


def print_processing_time(start_time):
    end_time = time.time()
    elapsed_time = end_time - start_time
    elapsed_timestamp = seconds_to_timestamp(int(elapsed_time))
    print(f"Processing took: {elapsed_timestamp}")


def sample_initial_colors(frame, blue_coords: Tuple[int, int, int, int], red_coords: Tuple[int, int, int, int]) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    blue_color = sample_color(frame, blue_coords)
    red_color = sample_color(frame, red_coords)
    print()
    print("Sampled initial colors blue: " +
          str(blue_color) + " red: " + str(red_color))
    return blue_color, red_color


def sample_color(image: np.ndarray, coordinates) -> Tuple[int, int, int]:
    x, y, w, h = coordinates
    # Scan area that was input and calculate average color in that space
    color_sample = image[y:y+h, x:x+w]

    # Compute the average color of the sub-image
    avg_color = np.mean(color_sample, axis=(0, 1))

    # Convert the average color from BGR to RGB color space
    avg_color_rgb = (int(avg_color[2]), int(avg_color[1]), int(avg_color[0]))

    return avg_color_rgb


def print_progress_update(frame_count, fps, total_duration):
    current_time = frame_count / fps
    total_time = seconds_to_timestamp(total_duration)
    progress = seconds_to_timestamp(current_time)
    print(f"\rScanning video: {progress} / {total_time}", end="")
