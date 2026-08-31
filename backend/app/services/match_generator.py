import random
from app.models.match import Match, MatchState
from app.models.player import PlayerTypeEnum
import logging

logger = logging.getLogger(__name__)


def meme_proprietaire_humain(equipe_a, equipe_b) -> bool:
    return (
        equipe_a.id_owner == equipe_b.id_owner
        and equipe_a.owner.player_type == PlayerTypeEnum.humain
        and equipe_b.owner.player_type == PlayerTypeEnum.humain
    )


def resoudre_conflits_journee(paires: list[tuple]) -> list[tuple]:
    """Essaie de résoudre les paires interdites (même propriétaire humain)
    en échangeant des adversaires avec d'autres paires de la même journée."""
    paires = paires.copy()

    for k in range(len(paires)):
        a, b = paires[k]
        if not meme_proprietaire_humain(a, b):
            continue  # cette paire est valide, rien à faire

        resolu = False
        for m in range(len(paires)):
            if m == k:
                continue
            c, d = paires[m]

            # Tentative 1 : échanger b <-> c
            if not meme_proprietaire_humain(a, c) and not meme_proprietaire_humain(b, d):
                paires[k] = (a, c)
                paires[m] = (b, d)
                resolu = True
                logger.info(f"Échange réussi pour résoudre le conflit : {a.nom} vs {b.nom} devient {a.nom} vs {c.nom}")
                break

            # Tentative 2 : échanger b <-> d
            if not meme_proprietaire_humain(a, d) and not meme_proprietaire_humain(c, b):
                paires[k] = (a, d)
                paires[m] = (c, b)
                logger.info(f"Échange réussi pour résoudre le conflit : {a.nom} vs {b.nom} devient {a.nom} vs {d.nom}")
                resolu = True
                break

        if not resolu:
            logger.warning(
                f"Impossible d'éviter la rencontre entre équipes du même propriétaire "
                f"({a.nom} vs {b.nom}) pour cette journée."
            )

    return paires


def generate_matches(equipes: list, total_journeys: int, allow_same_owner_matches: bool = True) -> list[Match]:
    matchs = []
    N = len(equipes)
    equipes = equipes.copy()
    random.shuffle(equipes)  # Mélange les équipes pour plus de variété

    for i in range(total_journeys):
        # 1. Construire les paires de la journée (sans encore créer de Match)
        paires = [
            (equipes[j], equipes[N - 1 - j])
            for j in range(N // 2)
        ]

        # 2. Corriger les paires interdites si l'option est désactivée
        if not allow_same_owner_matches:
            paires = resoudre_conflits_journee(paires)

        # 3. Créer les objets Match à partir des paires (corrigées ou non)
        for equipe_a, equipe_b in paires:
            match = Match(
                team_home_id=equipe_a.id,
                team_away_id=equipe_b.id,
                league_id=equipe_a.id_league,
                state=MatchState.pending,
                round_number=i + 1
            )
            matchs.append(match)

        # Rotation après chaque journée (inchangé)
        equipes = [equipes[0]] + [equipes[-1]] + equipes[1:-1]

    return matchs