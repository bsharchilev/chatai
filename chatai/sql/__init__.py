import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Define the engine (adjust the connection string to your database)
engine = create_engine(os.getenv("DATABASE_URI"))

# Create a configured "Session" class
Session = sessionmaker(bind=engine)
