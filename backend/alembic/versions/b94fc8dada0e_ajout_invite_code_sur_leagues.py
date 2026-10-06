"""ajout invite_code sur leagues

Revision ID: b94fc8dada0e
Revises: 3d9aedcfa439
Create Date: 2026-10-06 19:39:12.729700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import secrets

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sans 0, O, 1, I

def generer_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(6))


# revision identifiers, used by Alembic.
revision: str = 'b94fc8dada0e'
down_revision: Union[str, Sequence[str], None] = '3d9aedcfa439'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Étape 1 : colonne nullable, aucune contrainte
    op.add_column("leagues", sa.Column("invite_code", sa.String(6), nullable=True))

    # Étape 2 : un code distinct pour chaque ligue existante
    conn = op.get_bind()
    ids = conn.execute(sa.text("SELECT id FROM leagues")).scalars().all()
    deja_pris = set()
    for league_id in ids:
        code = generer_code()
        while code in deja_pris:
            code = generer_code()
        deja_pris.add(code)
        conn.execute(
            sa.text("UPDATE leagues SET invite_code = :code WHERE id = :id"),
            {"code": code, "id": league_id},
        )

    # Étape 3 : on verrouille
    op.alter_column("leagues", "invite_code", nullable=False)
    op.create_unique_constraint("uq_leagues_invite_code", "leagues", ["invite_code"])


def downgrade() -> None:
    op.drop_constraint("uq_leagues_invite_code", "leagues", type_="unique")
    op.drop_column("leagues", "invite_code")
