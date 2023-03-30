from typing import List
from classes import Kill
from exporter import seconds_to_timestamp
from utils import timestamp_to_seconds
import cv2
import numpy as np
from typing import List, Tuple
# from config import video, templates_folder_path, kill_feed_coords
from config import templates_folder_path, kill_feed_coords  # GUI CONFIG
import torchvision.transforms as T
import os
from helpers import sample_color


class KillProcessor:
    '''
    def __init__(self, models, match):
        self.unconfirmed_kills: List[Kill] = []
        self.confirmed_kills: List[Kill] = []
        self.new_kills: List[Kill] = []
        self.models = models
        self.current_kf_image = None  # each frame gets updated. Image of current state of KF
        self.kill_feed_coords = kill_feed_coords
        self.current_kill_entries = None
        # how many times we have to find same entry before we confirm a kill
        self.confirmation_contingency = 3
        self.match = match
    '''

    def __init__(self, models, match, video):
        self.unconfirmed_kills: List[Kill] = []
        self.confirmed_kills: List[Kill] = []
        self.new_kills: List[Kill] = []
        self.models = models
        self.current_kf_image = None  # each frame gets updated. Image of current state of KF
        self.kill_feed_coords = kill_feed_coords
        self.current_kill_entries = None
        # how many times we have to find same entry before we confirm a kill
        self.confirmation_contingency = 3
        self.match = match
        self.video = video

    def update_current_kf_image(self, frame):
        x, y, w, h = self.kill_feed_coords
        self.current_kf_image = frame[y:y+h, x:x+w]

    def process_kill_entries(self, blue_color: Tuple[int, int, int], red_color: Tuple[int, int, int]) -> List[Kill]:
        # where we are in the video
        timestamp = seconds_to_timestamp(
            int(self.video.get(cv2.CAP_PROP_POS_MSEC) / 1000))
        # pair kill entries into (killer, victim) pairs. In coordinates (x, y, w ,h).
        paired_kill_entries, unpaired_victims = self.pair_kill_entries(
            self.current_kill_entries)
        kills = self.convert_entries_to_kill_objects(
            paired_kill_entries, unpaired_victims, self.current_kf_image, blue_color, red_color, timestamp)

        self.new_kills = kills
        return kills

    def convert_entries_to_kill_objects(self, paired_kill_entries, unpaired_victims, image, blue_color, red_color, timestamp):
        kills = []
        for pair in paired_kill_entries:
            killer, victim = pair
            killer_x, killer_y, killer_w, killer_h, _ = killer
            victim_x, victim_y, victim_w, victim_h, _ = victim

            killer_entry = image[killer_y:killer_y +
                                 killer_h, killer_x:killer_x+killer_w]
            victim_entry = image[victim_y:victim_y +
                                 victim_h, victim_x:victim_x+victim_w]

            killer_icon = self.find_hero_icon(killer_entry)

            victim_icon = self.find_hero_icon(victim_entry)

            killer_color = self.get_kill_entry_color(
                image, killer_x, killer_y, killer_w, killer_h, blue_color, red_color, "killer")
            victim_color = self.get_kill_entry_color(
                image, victim_x, victim_y, victim_w, victim_h, blue_color, red_color, "victim")

            # using CV extract hero icon from this
            killer_hero, killer_confidence = self.models.scan_hero_kf(
                killer_icon)
            victim_hero, victim_confidence = self.models.scan_hero_kf(
                victim_icon)

            # debug to check if predictions are bad. Probably gotta do something else here such as ignore.
            if killer_confidence < 0.8:
                print(
                    f"Killer {killer_hero} predicted at {killer_confidence} {timestamp}")

            if victim_confidence < 0.8:
                print(
                    f"Victim {victim_hero} predicted at {victim_confidence} {timestamp}")

            if self.is_kill_possible(killer_hero, killer_color, victim_hero, victim_color):
                # create kill objects. If colors are same its a resurrect
                if killer_color == victim_color:
                    # check if killer hero is mercy, otherwise the model most likely read colors wrong and we should ignore
                    if killer_hero == "mercy":
                        kill = Kill(timestamp, killer_hero, victim_hero,
                                    killer_color, victim_color, resurrect=True)
                    else:
                        continue
                else:
                    kill = Kill(timestamp, killer_hero, victim_hero,
                                killer_color, victim_color)
                kills.append(kill)

        for victim in unpaired_victims:
            victim_x, victim_y, victim_w, victim_h, _ = victim
            victim_entry = image[victim_y:victim_y +
                                 victim_h, victim_x:victim_x+victim_w]
            victim_icon = self.find_hero_icon(victim_entry)
            victim_color = self.get_kill_entry_color(
                image, victim_x, victim_y, victim_w, victim_h, blue_color, red_color, "victim")
            victim_hero, victim_confidence = self.models.scan_hero_kf(
                victim_icon)

            if victim_confidence < 0.8:
                print(
                    f"Suicide Victim {victim_hero} predicted at {victim_confidence} {timestamp}")

            kill = Kill(timestamp, None, victim_hero,
                        None, victim_color, suicide=True)
            kills.append(kill)
        return kills

    def find_hero_icon(self, kill_entry: np.ndarray) -> np.ndarray:
        # Take in a kill entry in the kill feed and extract just the hero image using CV template matching
        # Can probably speed this up by training model better.
        kill_entry_gray = cv2.cvtColor(kill_entry, cv2.COLOR_BGR2GRAY)
        templates_folder = templates_folder_path
        max_corr = -1
        best_match = None
        had_to_resize = False

        for template_file in os.listdir(templates_folder):
            template = cv2.imread(os.path.join(
                templates_folder, template_file), cv2.IMREAD_GRAYSCALE)
            # should be 30,30 all of the time
            h, w = template.shape

            if kill_entry_gray.shape[0] < h:
                kill_entry_gray = self.resize_kill_entry(kill_entry_gray, h)
                had_to_resize = True

            result = cv2.matchTemplate(
                kill_entry_gray, template, cv2.TM_CCOEFF_NORMED)

            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val > max_corr:
                max_corr = max_val
                best_match = kill_entry[max_loc[1]:max_loc[1] + h, max_loc[0]:max_loc[0] + w]

            if had_to_resize:
                cv2.imwrite("debug/Kill_entry_gray.png", kill_entry_gray)
                cv2.imwrite("debug/Best Match.png", best_match)
        return best_match

    def resize_kill_entry(self, kill_entry_gray, h):
        # runs if model spits out a match that is smaller than 30px in height.
        # if h under 30, cv2 can't match against it since template is 30x30
        old_width = kill_entry_gray.shape[1]
        new_height = max(h+1, kill_entry_gray.shape[0])
        kill_entry_gray = cv2.resize(
            kill_entry_gray, (old_width, new_height))
        print("Had to resize kill entry. Logged in debug.")
        print(f"resized shape {kill_entry_gray.shape}")
        return kill_entry_gray

    def get_kill_entry_color(self, image: np.ndarray, x: int, y: int, w: int, h: int, blue_color: Tuple[int, int, int], red_color: Tuple[int, int, int], id: str) -> str:
        # will scan a 4x2 pixel area inside the kill entry, and see if its closer to red or blue
        # custom areas based on if it's killer or victim, since the images are inversed based on that
        if id == "killer":
            sample_width, sample_height = 4, 2
            sample_x = x + 11
            sample_y = y + 28
        if id == "victim":
            sample_width, sample_height = 4, 2
            sample_x = x + w - 19
            sample_y = y + h - 7

        sampled_color = sample_color(
            image, (sample_x, sample_y, sample_width, sample_height))
        '''
        # debug to visualize where im sampling
        debug_image = image.copy()
        cv2.rectangle(debug_image, (sample_x, sample_y), (sample_x +
                    sample_width, sample_y + sample_height), (0, 255, 0), 1)
        cv2.imshow('Sample Area', debug_image)
        cv2.waitKey(0)
        '''
        # calculate if the color is closer to red or blue
        blue_distance = np.sqrt(
            np.sum((np.array(blue_color) - np.array(sampled_color)) ** 2))
        red_distance = np.sqrt(
            np.sum((np.array(red_color) - np.array(sampled_color)) ** 2))

        return 'blue' if blue_distance < red_distance else 'red'

    def pair_kill_entries(self, kill_entries):
        paired_kill_entries = []
        unpaired_victims = []
        # to keep track of indexes that have been paired. set doesnt allow for same values
        paired_indices = set()
        for i, entry in enumerate(kill_entries):
            # model returns coordinates for top left and bottom left corner
            x, y, x2, y2 = entry.astype(int)
            # to get width and height of each box, we have to deduct bottom right corner from top left corner
            w, h = x2-x, y2-y
            entry_info = (x, y, w, h, i)
            paired = False
            for j, other_entry in enumerate(kill_entries):
                if i != j and j not in paired_indices:
                    other_x, other_y, other_x2, other_y2 = other_entry.astype(
                        int)
                    other_w, other_h = other_x2 - other_x, other_y2 - other_y,
                    if abs(y - other_y) <= 15:
                        # Determine which entry is on the left (killer) and right (victim)
                        left_entry = entry_info if x < other_x else (
                            other_x, other_y, other_w, other_h, j)
                        right_entry = entry_info if x >= other_x else (
                            other_x, other_y, other_w, other_h, j)
                        paired_kill_entries.append((left_entry, right_entry))
                        paired = True
                        paired_indices.add(j)
                        paired_indices.add(i)
                        '''
                        print()
                        print("Pairing happened: Killer x,y : " +
                              str(left_entry[0]+1354) + ", " + str(left_entry[1]+159) + " " + "Victim x,y: " + str(right_entry[0]+1354) + ", " + str(right_entry[1]+159))
                        '''
                        break
            # we havent found match close enough, means this is a suicide (no killer)
            if not paired and i not in paired_indices:
                unpaired_victims.append(entry_info)

        return paired_kill_entries, unpaired_victims

    def get_and_update_kill_entries(self) -> List[np.ndarray]:
        # transform image to model format, move image to GPU/device
        transform = T.Compose([T.ToTensor()])
        transformed_image = transform(self.current_kf_image).unsqueeze(
            0).to(self.models.ke_device)
        detections = self.models.kill_entry_finder(transformed_image)[0]
        kill_entries = []
        for i in range(len(detections['boxes'])):
            if detections['scores'][i] > 0.5:  # how sure the model is it found the entry
                box = detections['boxes'][i].detach().cpu().numpy()
                kill_entries.append(box)
        self.current_kill_entries = kill_entries
        return kill_entries

    def kill_in_unconfirmed(self, new_kill: Kill, current_frame: int) -> bool:
        found = False
        for unconfirmed_kill in self.unconfirmed_kills:
            # if killer and victim hero and colors are same
            if unconfirmed_kill.is_same_kill(new_kill):
                found = True
                unconfirmed_kill.increment_counter()
                unconfirmed_kill.update_last_detected_frame(current_frame)

                if unconfirmed_kill.counter >= self.confirmation_contingency:
                    self.modify_kd_stats(unconfirmed_kill)
                    self.confirmed_kills.append(unconfirmed_kill)
                    self.unconfirmed_kills.remove(unconfirmed_kill)
                break
        return found

    def modify_kd_stats(self, kill):
        # Find the killer's player and increment the kill count for their hero
        if kill.killer_color == "red":
            players_list = self.match.red_players
        else:
            players_list = self.match.blue_players

        for player in players_list:
            if player.current_hero is not None and player.current_hero.name == kill.killer_hero:
                player.current_hero.kills += 1
                break

        # Find the victim's player and increment the death count for their hero
        if kill.victim_color == "red":
            players_list = self.match.red_players
        else:
            players_list = self.match.blue_players

        for player in players_list:
            if player.current_hero is not None and player.current_hero.name == kill.victim_hero:
                player.current_hero.deaths += 1
                break

    def is_kill_possible(self, killer_hero, killer_color, victim_hero, victim_color):
        blue_hero_list = [
            player.current_hero.name for player in self.match.blue_players if player.current_hero is not None]
        red_hero_list = [
            player.current_hero.name for player in self.match.red_players if player.current_hero is not None]

        if killer_color == "red" and killer_hero in red_hero_list:
            if victim_color == "blue" and victim_hero in blue_hero_list:
                return True
        elif killer_color == "blue" and killer_hero in blue_hero_list:
            if victim_color == "red" and victim_hero in red_hero_list:
                return True

        return False

    def process_kills(self, current_frame: int):
        for new_kill in self.new_kills:
            # looks for kill in unconfirmed. Also moves to confirmed if contingency met
            found = self.kill_in_unconfirmed(new_kill, current_frame)
            # if we dont find kill in unconfirmed list, below runs
            if not found:
                cooldown_passed = True
                # this flag needed to ensure we scan through entire confirmed kills list before breaking
                # if same kill happened  30 seconds ago and 5 seconds ago, it ensures that it doesn't break the loop after finding the kill 30 seconds ago
                kill_already_processed = False
                for confirmed_kill in self.confirmed_kills:
                    if confirmed_kill.is_same_kill(new_kill):
                        # how long passed since this kill was added to confirmed
                        time_difference = abs(timestamp_to_seconds(
                            new_kill.timestamp) - timestamp_to_seconds(confirmed_kill.timestamp))
                        if time_difference <= 8:
                            kill_already_processed = True
                            break

                cooldown_passed = not kill_already_processed

                if cooldown_passed:
                    new_kill.increment_counter()
                    new_kill.update_last_detected_frame(current_frame)
                    self.unconfirmed_kills.append(new_kill)
        self.clear_unconfirmed(current_frame)

    def clear_unconfirmed(self, current_frame: int):
        # Remove kills from unconfirmed if the kill hasnt been spotted on consecutive frames
        for unconfirmed_kill in self.unconfirmed_kills:
            if unconfirmed_kill.last_detected_frame - current_frame < 0:
                self.unconfirmed_kills.remove(unconfirmed_kill)

    def move_unc_to_conf(self):
        how_many_moved = 0
        for kill in self.unconfirmed_kills:
            self.confirmed_kills.append(kill)
            how_many_moved += 1
        print(
            f"Moved {how_many_moved} entries from unconfirmed to confirmed at the end of the video.")
