import pandas as pd
from classes import Hero
from config import hero_switches_output, low_confidence_output, hero_playtime_output, kill_log_output
from datetime import datetime
from typing import List
from classes import Kill
from utils import timestamp_to_seconds


def seconds_to_timestamp(seconds: int) -> str:
    # Converts seconds into a timestamp string in the format HH:MM:SS.
    return str(datetime.utcfromtimestamp(seconds).strftime('%H:%M:%S'))


def export_output(hero_switches, all_players, models, kill_processor):

    save_to_csv(hero_switches, hero_switches_output, [
                "name", "previous hero", "new hero", "time"])

    save_to_csv(models.low_confidence, low_confidence_output,
                ["hero", "certainty", "time"])
    save_heroes_played_to_csv(all_players, hero_playtime_output)

    kill_list_to_txt_file(kill_processor.confirmed_kills, kill_log_output)


def kill_list_to_txt_file(kills: List[Kill], filename: str):
    with open(filename, "w") as file:
        for kill in kills:
            file.write(str(kill) + "\n")


def save_to_csv(data, filename, column_names):
    formatted_data = []

    for entry in data:

        formatted_entry = {}
        for key, value in entry.items():
            if isinstance(value, Hero):
                formatted_entry[key] = value.name
            else:
                formatted_entry[key] = value
        formatted_data.append(formatted_entry)

    df = pd.DataFrame(formatted_data)
    # Add this line to print the columns in the DataFrame
    df.to_csv(filename, index=False, columns=column_names)


def save_heroes_played_to_csv(players, filename):
    # create object entries to summarize player. Each entry is each players heroes that he played and its info
    data = [{"player_name": player.name, "hero_name": hero.name, "time_played": round(hero.time_played), "kills": hero.kills, "deaths": hero.deaths}
            for player in players
            for hero in player.heroes_played]
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, columns=[
              "player_name", "hero_name", "time_played", "kills", "deaths"])
