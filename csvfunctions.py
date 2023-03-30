import pandas as pd


def save_heroes_played_to_csv(players, filename):
    data = [{"player_name": player.name, "hero_name": hero, "time_played": time_played}
            for player in players
            for hero, time_played in player.heroes_played]
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, columns=[
              "player_name", "hero_name", "time_played"])


def save_to_csv(data, filename, column_names):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, columns=column_names)
