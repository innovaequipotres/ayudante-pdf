"""add document_edits, observation_states and editing status

Revision ID: 8f3c2a1d9e4b
Revises: 2c7ed37d671b
Create Date: 2026-11-28 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f3c2a1d9e4b"
down_revision: str | Sequence[str] | None = "2c7ed37d671b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crea las tablas de ediciones y estados, y habilita el estado editing."""
    op.create_table(
        "document_edits",
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("block_id", sa.String(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(btrim(text)) > 0",
            name="ck_document_edits_text_not_blank",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("document_id", "block_id"),
    )
    op.create_index(
        "ix_document_edits_owner", "document_edits", ["owner_id"], unique=False
    )

    op.create_table(
        "observation_states",
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("observation_id", sa.String(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column(
            "state",
            sa.String(),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "state IN ('pending', 'applied', 'ignored')",
            name="ck_observation_states_state",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("document_id", "observation_id"),
    )
    op.create_index(
        "ix_observation_states_owner", "observation_states", ["owner_id"], unique=False
    )

    # El estado "editing" amplía el CHECK de documents.status.
    op.drop_constraint("ck_documents_status", "documents", type_="check")
    op.create_check_constraint(
        "ck_documents_status",
        "documents",
        "status IN ('uploaded', 'extracted', 'analyzed', 'editing', 'completed')",
    )


def downgrade() -> None:
    """Revierte el estado editing y elimina las tablas de ediciones."""
    op.drop_constraint("ck_documents_status", "documents", type_="check")
    op.create_check_constraint(
        "ck_documents_status",
        "documents",
        "status IN ('uploaded', 'extracted', 'analyzed', 'completed')",
    )

    op.drop_index("ix_observation_states_owner", table_name="observation_states")
    op.drop_table("observation_states")

    op.drop_index("ix_document_edits_owner", table_name="document_edits")
    op.drop_table("document_edits")