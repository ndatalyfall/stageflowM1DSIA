"""Base declarative et import des modeles SQLAlchemy."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
	"""Classe de base de toutes les tables de l'application."""

