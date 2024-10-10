from sqlalchemy import BigInteger, Numeric, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class Message(Base):
    __tablename__ = 'messages'

    id = Column(BigInteger, primary_key=True, autoincrement=False)
    chat_id = Column(BigInteger, nullable=True)
    username = Column(String, nullable=True)
    text = Column(String, nullable=True)
    unixtime = Column(Integer, nullable=True)
    image_b64_encoded = Column(String, nullable=True)
    reply_to_message_id = Column(BigInteger, nullable=True)

    def __repr__(self):
        fields = {col.name: getattr(self, col.name) for col in self.__table__.columns}
        return f"<{self.__class__.__name__}({fields})>"

class Memory(Base):
    __tablename__ = 'memories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=True)
    start_unixtime = Column(Integer, nullable=True)
    end_unixtime = Column(Integer, nullable=True)
    character_name = Column(String, nullable=True)
    fact = Column(String, nullable=True)
    interest_score = Column(Numeric, nullable=True)

    def __repr__(self):
        fields = {col.name: getattr(self, col.name) for col in self.__table__.columns}
        return f"<{self.__class__.__name__}({fields})>"
