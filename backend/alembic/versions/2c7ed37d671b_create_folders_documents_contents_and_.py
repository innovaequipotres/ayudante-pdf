"""create folders, documents, extracted contents and diagnoses

Revision ID: 2c7ed37d671b
Revises: 7d53671050aa
Create Date: 2026-11-26 14:55:39.848837

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2c7ed37d671b"
down_revision: str | Sequence[str] | None = "7d53671050aa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crea las tablas de carpetas, documentos y análisis.

    Los enums del dominio se guardan como texto con CHECK, no como tipos
    nativos de PostgreSQL.
    """
    op.create_table(
        "folders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
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
            "length(btrim(name)) > 0",
            name="ck_folders_name_not_blank",
        ),
        sa.CheckConstraint("name = btrim(name)", name="ck_folders_name_trimmed"),
        sa.CheckConstraint(
            "parent_id IS NULL OR parent_id <> id",
            name="ck_folders_not_self_parent",
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["folders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_folders_owner_parent",
        "folders",
        ["owner_id", "parent_id"],
        unique=False,
    )
    # Dos índices parciales: un índice único común no detecta duplicados en las
    # raíces porque parent_id NULL nunca colisiona con otro NULL.
    op.create_index(
        "uq_folders_owner_parent_name",
        "folders",
        ["owner_id", "parent_id", sa.literal_column("lower(name)")],
        unique=True,
        postgresql_where=sa.text("parent_id IS NOT NULL"),
    )
    op.create_index(
        "uq_folders_owner_root_name",
        "folders",
        ["owner_id", sa.literal_column("lower(name)")],
        unique=True,
        postgresql_where=sa.text("parent_id IS NULL"),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("folder_id", sa.UUID(), nullable=True),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.String(),
            server_default=sa.text("'uploaded'"),
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
            "source_type IN ('pdf', 'text')",
            name="ck_documents_source_type",
        ),
        sa.CheckConstraint(
            "status IN ('uploaded', 'extracted', 'analyzed', 'completed')",
            name="ck_documents_status",
        ),
        sa.CheckConstraint(
            "size_bytes >= 0",
            name="ck_documents_size_bytes_non_negative",
        ),
        sa.ForeignKeyConstraint(["folder_id"], ["folders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_documents_owner_created_at",
        "documents",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_documents_owner_folder",
        "documents",
        ["owner_id", "folder_id"],
        unique=False,
    )

    op.create_table(
        "document_files",
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "(content IS NOT NULL) <> (content_text IS NOT NULL)",
            name="ck_document_files_one_content",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("document_id"),
    )
    op.create_index(
        "ix_document_files_owner",
        "document_files",
        ["owner_id"],
        unique=False,
    )

    op.create_table(
        "extracted_contents",
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
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
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("document_id"),
    )
    op.create_index(
        "ix_extracted_contents_owner",
        "extracted_contents",
        ["owner_id"],
        unique=False,
    )

    op.create_table(
        "diagnoses",
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("score", sa.SmallInteger(), nullable=False),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column(
            "ai_status",
            sa.String(),
            server_default=sa.text("'skipped'"),
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
            "score >= 0 AND score <= 100",
            name="ck_diagnoses_score_range",
        ),
        sa.CheckConstraint(
            "level IN ('ok', 'review', 'barrier')",
            name="ck_diagnoses_level",
        ),
        sa.CheckConstraint(
            "ai_status IN ('ok', 'unavailable', 'skipped')",
            name="ck_diagnoses_ai_status",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("document_id"),
    )
    op.create_index("ix_diagnoses_owner", "diagnoses", ["owner_id"], unique=False)


def downgrade() -> None:
    """Elimina las tablas en el orden inverso a su creación."""
    op.drop_index("ix_diagnoses_owner", table_name="diagnoses")
    op.drop_table("diagnoses")

    op.drop_index("ix_extracted_contents_owner", table_name="extracted_contents")
    op.drop_table("extracted_contents")

    op.drop_index("ix_document_files_owner", table_name="document_files")
    op.drop_table("document_files")

    op.drop_index("ix_documents_owner_folder", table_name="documents")
    op.drop_index("ix_documents_owner_created_at", table_name="documents")
    op.drop_table("documents")

    op.drop_index(
        "uq_folders_owner_root_name",
        table_name="folders",
        postgresql_where=sa.text("parent_id IS NULL"),
    )
    op.drop_index(
        "uq_folders_owner_parent_name",
        table_name="folders",
        postgresql_where=sa.text("parent_id IS NOT NULL"),
    )
    op.drop_index("ix_folders_owner_parent", table_name="folders")
    op.drop_table("folders")
