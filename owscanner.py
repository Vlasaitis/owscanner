from classes import Hero, Match
from models import Models
from scanners import TopBarScanner, KillFeedScanner
from config import player_csv, top_bar_interval, hero_swap_contingency, blue_color_sample_coords, red_color_sample_coords, video_to_parse
# from config import hero_swap_contingency, blue_color_sample_coords, red_color_sample_coords
from exporter import export_output
from processors import KillProcessor
from helpers import sample_initial_colors, print_progress_update, print_processing_time, instantiate_video_variables
import time
import cv2

pause_intervals = [(178, 202), (422, 451)]
# pause_intervals = [(0, 0)]

# def process_video(video):


def process_video(video, players_csv):
    total_frames, fps, total_duration, top_bar_interval, kf_interval = instantiate_video_variables(
        video)

    # above is when GUI is running
    start_time = time.time()
    current_frame_nr = 0
    timestamp = 0
    models = Models()  # initiate object that holds all the models for scanning
    # initiate the match object. Scan in players, create and manipulate player and hero objects
    match = Match(players_csv, top_bar_interval, hero_swap_contingency, fps)
    # tracks unconfirmed/confirmed kills
    # kill_processor = KillProcessor(models, match) # when i am not using the gui
    kill_processor = KillProcessor(models, match, video)
    # Create scanners, need the models and the match objects to scan and manipulate match objects based on what it sees
    scanner_top = TopBarScanner(models, match)
    scanner_kf = KillFeedScanner(models, match)

    paused = False
    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break

        current_frame_nr += 1
        timestamp = current_frame_nr / fps
        print_progress_update(current_frame_nr, fps, total_duration)

        # Check if the current timestamp is within the pause intervals
        if match.is_paused(timestamp, pause_intervals):
            # runs once the moment the game is paused. Update playing time.
            if not paused:
                match.pause_players(timestamp)
                paused = True
                print("Scanning paused")
            continue
        elif paused:  # run this the first frame that game is unpaused
            match.update_all_timestamp_at_swap(timestamp)
            print("Scanning resumes")
            paused = False

        # only runs first frame to sample team colors
        if current_frame_nr == 1:
            match.blue_color, match.red_color = sample_initial_colors(
                frame, blue_color_sample_coords, red_color_sample_coords)
        # scan top bar and adjust the objects
        if current_frame_nr % top_bar_interval == 0:
            scanner_top.scan_top_bar(frame, timestamp)

        if current_frame_nr % kf_interval == 0:
            scanner_kf.scan_kill_feed(
                frame, kill_processor, match, current_frame_nr)

    video.release()

    # probably remove this later once round end detection implemented
    kill_processor.move_unc_to_conf()
    match.update_all_time_played(match.players, timestamp)
    print_processing_time(start_time)
    return match.hero_switches, match.players, models, kill_processor


def main():
    video = cv2.VideoCapture(video_to_parse)
    hero_switches, all_players, models, kill_processor = process_video(
        video, player_csv)
    export_output(hero_switches, all_players, models, kill_processor)


'''
#Main Method when using the GUI
def main(video_path=None, players_path=None, progress_queue=None):
    # Load the video path and players from the files if not provided as arguments

    print("video_path after passing: " + video_path)
    video = cv2.VideoCapture(video_path)

    hero_switches, all_players, models, kill_processor = process_video(
        video, progress_queue, players_path)
    export_output(hero_switches, all_players, models, kill_processor)

    # for the GUI this goes into progress_video
        # Update progress bar every 1 second
        if current_frame_nr % (fps * 5) == 0:
            progress_queue.put((current_frame_nr, total_frames))
'''


if __name__ == '__main__':
    main()
