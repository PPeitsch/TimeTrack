from flask import g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app.config.config import Config
from app.models.models import Base

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)

    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Base.metadata.create_all(engine)

    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    return Session()


def get_db():
    if "db" not in g:
        g.db = Session()
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
