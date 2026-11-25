"""baseline

Revision ID: f4e6032f4c53
Revises:
Create Date: 2026-11-25 18:31:43.062403

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "f4e6032f4c53"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
