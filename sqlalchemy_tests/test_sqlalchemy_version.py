"""test_sqlalchemy_version.py — SQLAlchemy version and import validation."""
import sqlalchemy


def test_sqlalchemy_version():
    """SQLAlchemy exposes a version string."""
    assert sqlalchemy.__version__


def test_sqlalchemy_core_imports():
    """SQLAlchemy core components import successfully."""
    from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String
    assert create_engine
    assert text
