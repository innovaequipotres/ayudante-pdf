import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.document import Document
from app.models.folder import Folder
from app.models.user import User
from app.schemas.session import SourceType


def _create_user(db_session, email: str | None = None) -> User:
    user = User(
        first_name="Docente",
        last_name="Demo",
        email=email or f"docente-{uuid.uuid4()}@example.com",
        password_hash="hash-de-prueba",
    )
    db_session.add(user)
    db_session.commit()
    return user


def _create_folder(
    db_session,
    owner: User,
    name: str,
    parent: Folder | None = None,
) -> Folder:
    folder = Folder(
        owner_id=owner.id,
        parent_id=parent.id if parent else None,
        name=name,
    )
    db_session.add(folder)
    db_session.commit()
    return folder


def test_duplicate_root_name_is_rejected_case_insensitively(db_session):
    owner = _create_user(db_session)
    _create_folder(db_session, owner, "Matemática")

    duplicate = Folder(owner_id=owner.id, name="matemática")
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_duplicate_name_under_same_parent_is_rejected(db_session):
    owner = _create_user(db_session)
    parent = _create_folder(db_session, owner, "Ciencias")
    _create_folder(db_session, owner, "Unidad 1", parent=parent)

    duplicate = Folder(owner_id=owner.id, parent_id=parent.id, name="unidad 1")
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_same_name_under_different_parents_is_allowed(db_session):
    owner = _create_user(db_session)
    first_parent = _create_folder(db_session, owner, "Ciencias")
    second_parent = _create_folder(db_session, owner, "Historia")

    first = _create_folder(db_session, owner, "Unidad 1", parent=first_parent)
    second = _create_folder(db_session, owner, "Unidad 1", parent=second_parent)

    assert first.name == second.name
    assert first.parent_id != second.parent_id


def test_same_root_name_in_different_owners_is_allowed(db_session):
    first_owner = _create_user(db_session)
    second_owner = _create_user(db_session)

    first = _create_folder(db_session, first_owner, "Matemática")
    second = _create_folder(db_session, second_owner, "Matemática")

    assert first.name == second.name
    assert first.owner_id != second.owner_id


def test_same_name_in_root_and_nested_folder_is_allowed(db_session):
    owner = _create_user(db_session)
    root = _create_folder(db_session, owner, "Matemática")
    parent = _create_folder(db_session, owner, "Ciencias")
    nested = _create_folder(db_session, owner, "Matemática", parent=parent)

    assert root.parent_id is None
    assert nested.parent_id == parent.id
    assert root.name == nested.name


def test_folder_name_is_trimmed_on_save(db_session):
    owner = _create_user(db_session)
    folder = _create_folder(db_session, owner, "  Matemática  ")

    assert folder.name == "Matemática"


def test_folder_name_with_surrounding_spaces_is_rejected_in_database(db_session):
    owner = _create_user(db_session)

    with pytest.raises(IntegrityError):
        db_session.execute(
            text(
                "INSERT INTO folders (id, owner_id, name) "
                "VALUES (:id, :owner_id, :name)"
            ),
            {
                "id": uuid.uuid4(),
                "owner_id": owner.id,
                "name": "  Matemática  ",
            },
        )
    db_session.rollback()


def test_blank_folder_name_is_rejected(db_session):
    owner = _create_user(db_session)

    blank = Folder(owner_id=owner.id, name="   ")
    db_session.add(blank)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_folder_cannot_be_its_own_parent(db_session):
    owner = _create_user(db_session)
    folder = Folder(owner_id=owner.id, name="Autoreferencia")
    db_session.add(folder)
    db_session.flush()

    folder.parent_id = folder.id
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_deleting_folder_moves_documents_to_root(db_session):
    owner = _create_user(db_session)
    folder = _create_folder(db_session, owner, "Matemática")
    document = Document(
        owner_id=owner.id,
        folder_id=folder.id,
        source_type=SourceType.PDF.value,
        filename="material.pdf",
        size_bytes=10,
    )
    db_session.add(document)
    db_session.commit()

    db_session.delete(folder)
    db_session.commit()
    db_session.expire_all()

    assert db_session.get(Folder, folder.id) is None
    stored_document = db_session.get(Document, document.id)
    assert stored_document is not None
    assert stored_document.folder_id is None


def test_deleting_parent_folder_cascades_to_children(db_session):
    owner = _create_user(db_session)
    parent = _create_folder(db_session, owner, "Ciencias")
    child = _create_folder(db_session, owner, "Unidad 1", parent=parent)
    parent_id = parent.id
    child_id = child.id

    db_session.delete(parent)
    db_session.commit()
    db_session.expire_all()

    assert db_session.get(Folder, parent_id) is None
    assert db_session.get(Folder, child_id) is None
