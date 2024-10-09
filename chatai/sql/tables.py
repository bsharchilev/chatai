from sqlalchemy import BigInteger, Column, Integer, String
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