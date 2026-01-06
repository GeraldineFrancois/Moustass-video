from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# adapte user / password / db_name
DATABASE_URL = "mysql+pymysql://root:MyStrongP%40ss123%21@localhost:3306/videos_db"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
