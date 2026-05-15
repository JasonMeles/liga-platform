import random
from app.models.match import Match, MatchState

def generate_matches(equipes: list, total_journeys: int) -> list[Match]:
    matchs = []
    N = len(equipes)
    equipes = equipes.copy()  # on ne modifie pas la liste originale

    for i in range(total_journeys):
        for j in range(N // 2):
            match = Match(
                team_home_id=equipes[j].id,
                team_away_id=equipes[N - 1 - j].id,
                league_id=equipes[0].id_league,
                state=MatchState.pending,
                round_number=i + 1
            )
            matchs.append(match)

        # Rotation après chaque journée
        equipes = [equipes[0]] + [equipes[-1]] + equipes[1:-1]

    return matchs