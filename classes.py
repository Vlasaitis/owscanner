import pandas as pd
from utils import timestamp_to_seconds
from config import dps_heroes, support_heroes, tank_heroes


class Kill:
    def __init__(self, timestamp: str, killer_hero: str, victim_hero: str, killer_color: str, victim_color: str, suicide=False, resurrect=False, counter=0, cooldown=3, last_detected_frame=0):
        self.timestamp = timestamp
        self.killer_hero = killer_hero
        self.victim_hero = victim_hero
        self.killer_color = killer_color
        self.victim_color = victim_color
        self.suicide = suicide
        self.resurrect = resurrect
        self.counter = counter
        self.cooldown = cooldown
        self.last_detected_frame = last_detected_frame

    def update_last_detected_frame(self, frame_number: int):
        self.last_detected_frame = frame_number

    def is_same_kill(self, kill) -> bool:
        return (self.killer_color == kill.killer_color and
                self.victim_color == kill.victim_color and
                self.killer_hero == kill.killer_hero and
                self.victim_hero == kill.victim_hero)

    def is_within_cooldown(self, other_kill: 'Kill'):
        time_difference = abs(timestamp_to_seconds(
            self.timestamp) - timestamp_to_seconds(other_kill.timestamp))
        return time_difference <= self.cooldown

    def increment_counter(self):
        self.counter += 1

    def __str__(self):
        if self.resurrect:
            return f"{self.timestamp}: {self.killer_color} {self.killer_hero} resurrected {self.victim_color} {self.victim_hero}"
        elif self.suicide:
            return f"{self.timestamp}: {self.victim_color} {self.victim_hero} killed himself"
        else:
            return f"{self.timestamp}: {self.killer_color} {self.killer_hero} eliminated {self.victim_color} {self.victim_hero}"


class Player:
    def __init__(self, name):
        self.name = name
        self.current_hero = None
        self.switch_counter = 0
        self.heroes_played = []  # list of Hero instances
        self.timestamp_at_swap = 0
        self.role = None

    def is_same_role(self, predicted_hero):
        if predicted_hero in dps_heroes and self.current_hero.name in dps_heroes:
            return True
        if predicted_hero in support_heroes and self.current_hero.name in support_heroes:
            return True
        if predicted_hero in tank_heroes and self.current_hero.name in tank_heroes:
            return True
        return False


class Hero:
    def __init__(self, name, kills=0, deaths=0, time_played=0):
        self.name = name
        self.kills = kills
        self.deaths = deaths
        self.time_played = time_played

    # equals function. If name of hero is same, its the same hero
    def __eq__(self, other):
        if isinstance(other, Hero):
            return self.name == other.name
        return False


class Match:
    def __init__(self, player_csv, top_bar_interval, hero_swap_contingency, fps):
        self.players = self.initialize_players(player_csv)
        self.frame_interval = top_bar_interval
        self.hero_swap_contingency = hero_swap_contingency
        self.fps = fps
        self.hero_switches = []
        self.blue_players = self.players[:5]
        self.red_players = self.players[5:]
        self.blue_color = None
        self.red_color = None
        self.kills = []

    def initialize_players(self, csv_filename):
        df = pd.read_csv(csv_filename, header=None)
        # format is player1, player2... iloc makes a list out of this row
        player_names = df.iloc[0].tolist()
        # list of empty player objects, just including the names. Other values get modified later.
        all_players = [Player(name) for name in player_names]
        return all_players

    def is_paused(self, timestamp, pause_intervals):
        for start, end in pause_intervals:
            if start <= timestamp <= end:
                return True
        return False

    def update_all_timestamp_at_swap(self, timestamp):
        for player in self.players:
            player.timestamp_at_swap = timestamp

    def pause_players(self, timestamp):
        for player in self.players:
            time_played = timestamp - player.timestamp_at_swap
            player.current_hero.time_played += time_played

    def update_player_attributes(self, player, timestamp, predicted_class, final_update=False):
        time_played = timestamp - player.timestamp_at_swap
        # Deduct 2.5 seconds for the new hero
        if not final_update:
            time_deduction = (self.frame_interval / self.fps) * \
                self.hero_swap_contingency
            time_played -= time_deduction
        current_hero_updated = False
        swapping_to_hero_already_played = False

        # does not run first iteration when setting initial heroes
        for index, played_hero in enumerate(player.heroes_played):
            # Before making swap, we update time played for hero being swapped from
            if played_hero.name == player.current_hero.name:
                played_hero.time_played += time_played
                current_hero_updated = True
            # If player swaps to a hero that's already played, set new_hero_added flag
            if played_hero.name == predicted_class:
                swapping_to_hero_already_played = True

        # runs only when selecting a first hero at the beginnning of round
        if not current_hero_updated and not swapping_to_hero_already_played:
            new_hero = Hero(predicted_class, time_played=time_played)
            player.heroes_played.append(new_hero)
        # runs every time after when swapping to a hero we havent already played.
        if current_hero_updated and not swapping_to_hero_already_played:
            new_hero = Hero(predicted_class, time_played=0)
            player.heroes_played.append(new_hero)

        self.reset_player_attributes_after_swap(
            player, timestamp, predicted_class)

    def reset_player_attributes_after_swap(self, player, timestamp, predicted_class):
        new_current_hero = [
            hero for hero in player.heroes_played if hero.name == predicted_class]
        player.current_hero = new_current_hero[0]
        player.timestamp_at_swap = timestamp
        player.switch_counter = 0

    def update_all_time_played(self, all_players, timestamp):
        for player in all_players:
            # time_played = timestamp - player.timestamp_at_swap
            # this is last update, so we can pass current_hero instead of predicted_class
            self.update_player_attributes(
                player, timestamp, player.current_hero.name, final_update=True)
