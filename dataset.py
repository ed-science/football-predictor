import csv
import datetime
from functools import reduce


class Dataset:
    def __init__(self, file_path):
        self.raw_results = []
        self.processed_results = []

        with open(file_path) as stream:
            reader = csv.DictReader(stream)

            for row in reader:
                row['Date'] = datetime.datetime.strptime(row['Date'], '%d/%m/%y')
                self.raw_results.append(row)

        for result in self.raw_results:
            home_statistics = self.get_statistics(result['HomeTeam'], result['Date'])

            if home_statistics is None:
                continue

            away_statistics = self.get_statistics(result['AwayTeam'], result['Date'])

            if away_statistics is None:
                continue

            processed_result = {
                'result': result['FTR'],
                'odds-home': float(result['B365H']),
                'odds-draw': float(result['B365D']),
                'odds-away': float(result['B365A']),
            }

            for label, statistics in [('home', home_statistics), ('away', away_statistics)]:
                for key in statistics.keys():
                    processed_result[f'{label}-{key}'] = statistics[key]

            self.processed_results.append(processed_result)

    # Filter results to only contain matches played in by a given team, before a given date
    def filter(self, team, date):
        def filter_fn(result):
            return (
                result['HomeTeam'] == team or
                result['AwayTeam'] == team
            ) and (result['Date'] < date)

        return list(filter(filter_fn, self.raw_results))

    # Calculate team statistics
    def get_statistics(self, team, date, matches=10):
        recent_results = self.filter(team, date)

        if len(recent_results) < matches:
            return None

        # This function maps a result to a set of performance measures roughly scaled between -1 and 1
        def map_fn(result):
            if result['HomeTeam'] == team:
                team_letter, opposition_letter = 'H', 'A'
                opposition = result['AwayTeam']
            else:
                team_letter, opposition_letter = 'A', 'H'
                opposition = result['HomeTeam']

            goals = int(result[f'FT{team_letter}G'])
            shots = int(result[f'{team_letter}S'])
            shots_on_target = int(result[f'{team_letter}ST'])
            shot_accuracy = shots_on_target / shots if shots > 0 else 0

            opposition_goals = int(result[f'FT{opposition_letter}G'])
            opposition_shots = int(result[f'{opposition_letter}S'])
            opposition_shots_on_target = int(result[f'{opposition_letter}ST'])

            return {
                'wins': 1 if result['FTR'] == team_letter else 0,
                'draws': 1 if result['FTR'] == 'D' else 0,
                'losses': 1 if result['FTR'] == opposition_letter else 0,
                'goals': int(result[f'FT{team_letter}G']),
                'opposition-goals': int(result[f'FT{opposition_letter}G']),
                'shots': int(result[f'{team_letter}S']),
                'shots-on-target': int(result[f'{team_letter}ST']),
                'opposition-shots': int(result[f'{opposition_letter}S']),
                'opposition-shots-on-target': int(result[f'{opposition_letter}ST']),
            }

        def reduce_fn(x, y):
            return {key: x[key] + y[key] for key in x.keys()}

        return reduce(reduce_fn, map(map_fn, recent_results[-matches:]))
