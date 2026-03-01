# models.py
from sqlalchemy import Column, Integer, String, Date
from database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    notes = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    completed_date = Column(Date, nullable=True)
    status = Column(String)

    # These are not stored in DB; calculated in runtime
    duration = None
    spillover = None