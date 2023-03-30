from config import coordinates, hero_swap_contingency


class KillFeedScanner():
    def __init__(self, models, match):
        self.models = models
        self.match = match

    def scan_kill_feed(self, frame, kill_processor, match, current_frame_nr):
        kill_processor.update_current_kf_image(frame)
        # kill_entries = kill_processor.get_kill_entries()
        kill_processor.get_and_update_kill_entries()
        kill_processor.process_kill_entries(match.blue_color, match.red_color)
        kill_processor.process_kills(current_frame_nr)
        return


class TopBarScanner():
    def __init__(self, models, match):
        self.coordinates = coordinates
        self.first_scan = True
        self.models = models
        self.match = match

    def get_hero_image(self, frame, x, y):
        # passed coords are bottom right corner of hero bar image. This returns 38x38 of hero portrait
        x1, y1 = x - 38, y - 38
        x2, y2 = x, y
        return frame[y1:y2, x1:x2]

    def scan_top_bar(self, frame, timestamp):
        for i, coord in enumerate(self.coordinates):
            # each coord is (142, 110) format. *coord synta sends it in as a tuple
            hero_image = self.get_hero_image(frame, *coord)
            predicted_class, max_percentage = self.models.scan_hero_top(
                hero_image, timestamp)

            if self.first_scan:
                self.match.update_player_attributes(
                    self.match.players[i], timestamp, predicted_class)
            # this block runs every single frame of the video except for the first.
            else:
                player = self.match.players[i]

                # Contingency: make sure x amt of times player has swapped before registering it
                if predicted_class != player.current_hero.name:
                    self.check_contingencies_and_update_player(
                        predicted_class, player, self.match, timestamp)
                else:
                    # if its the same hero as previous scan, lets reset counter to 0
                    player.switch_counter = 0

        self.first_scan = False

    def check_contingencies_and_update_player(self, predicted_class, player, match, timestamp):
        # contingency to not increase the counter predicted is not same role
        if player.is_same_role(predicted_class):
            player.switch_counter += 1

            if player.switch_counter >= hero_swap_contingency:
                match.hero_switches.append(
                    {"name": player.name, "previous hero": player.current_hero.name, "new hero": predicted_class, "time": timestamp})
                match.update_player_attributes(
                    player, timestamp, predicted_class)

        else:
            player.switch_counter = 0


'''
class KillFeedScanner():
    def __init__(self):
        
'''
