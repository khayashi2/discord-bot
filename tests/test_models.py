"""Tests for database models."""

from db.models import Base, Channel, Member, Message


def test_all_models_have_tablenames():
    """Every model should define a __tablename__."""
    models = [Channel, Member, Message]
    for model in models:
        assert hasattr(model, "__tablename__")
        assert isinstance(model.__tablename__, str)


def test_base_metadata_contains_all_tables():
    """Base metadata should register all expected tables."""
    table_names = Base.metadata.tables.keys()
    expected = {"channels", "members", "messages"}
    assert expected.issubset(table_names)
