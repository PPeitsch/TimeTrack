from config.config import Config
from flask_sqlalchemy import SQLAlchemy
from models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)

    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    return Session()


def get_db():
    if "db" not in g:
        g.db = Session()
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
