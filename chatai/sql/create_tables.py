from chatai.sql import engine
from chatai.sql.tables import Base


if __name__ == "__main__":
    Base.metadata.create_all(engine)