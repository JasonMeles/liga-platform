from types import SimpleNamespace
from app.services.match_generator import generate_matches

def test_alternance_domicile_exterieur():
    # Arrange : deux fausses équipes, sans base de données
    equipe_1 = SimpleNamespace(id=1, id_league=1)
    equipe_2 = SimpleNamespace(id=2, id_league=1)

    # Act
    matchs = generate_matches([equipe_1, equipe_2], total_journeys=8)

    # Assert
    domicile_1 = len([m for m in matchs if m.team_home_id == equipe_1.id])
    domicile_2 = len([m for m in matchs if m.team_home_id == equipe_2.id])
    assert domicile_1 == 4
    assert domicile_2 == 4