import os
from sqlalchemy import create_engine

from chatai.sql.tables import Base


if __name__ == "__main__":
    database_uri = os.getenv("DATABASE_URI")
    engine = create_engine(database_uri)
    Base.metadata.create_all(engine)