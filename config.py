import cv2


def load_video_path():
    try:
        with open("video_path.csv", "r") as f:
            return f.readline().strip()
    except FileNotFoundError:
        return ""


# loading in players, video and setting fps and interval variables
player_csv = 'scrimplayers.csv'
# video_to_parse = 'scrimtest.mp4'
# video_to_parse = 'scrimedited.mov'
video_to_parse = 'iliostestpause.mp4'
# video_to_parse = load_video_path()
top_bar_interval_num = 0.5
kf_interval_num = 1

# model stuff
top_bar_model_path = 'models/topbarwithhack.h5'
kill_entry_path = 'models/kill_entry_detection.pth'
killfeed_model_path = 'models/killfeed.h5'
kill_entry_model_classes = 2
# cv uses these to isolate icons in kf entries
templates_folder_path = '1ofeachkf'
# output paths
hero_switches_output = 'output/hero_switches.csv'
low_confidence_output = 'output/low_confidence.csv'
hero_playtime_output = 'output/hero_playtime.csv'
kill_log_output = 'output/kills.txt'

# how many frames a hero swap has to be confirmed till player obj is updated
hero_swap_contingency = 5


# Hero Bar coordinates for each player, in order. 1920x1080 screen. Kill feed scans KF area
coordinates = [(142, 110), (248, 110), (354, 110), (460, 110), (566, 110),
               (1452, 110), (1558, 110), (1664, 110), (1770, 110), (1876, 110)]
kill_feed_coords = (1354, 159, 537, 219)
# Initial color sampling coordinates and dimensions. Scans top bar close to first hero on both sides
blue_color_sample_coords = (45, 104, 16, 5)
red_color_sample_coords = (1356, 104, 16, 5)

dps_heroes = ['ashe', 'bastion', 'cassidy', 'echo', 'genji', 'hanzo', 'junkrat', 'mei', 'pharah',
              'reaper', 's76', 'sojourn', 'sombra', 'symmetra', 'torbjorn', 'tracer', 'widowmaker']
support_heroes = ['ana', 'baptiste',  'kiriko',
                  'brigitte', 'lucio', 'mercy', 'moira', 'zenyatta']
tank_heroes = ['dva', 'hammond', 'orisa', 'doomfist', 'reinhardt',
               'roadhog', 'sigma', 'winston', 'zarya', 'junkerqueen', 'ramattra']
