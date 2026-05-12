from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class UserDesignPick(Base):
    __tablename__ = "user_design_picks"

    id = Column(Integer, primary_key=True, index=True)
    room_type = Column(String, index=True)
    theme = Column(String, index=True)
    width_m = Column(Float)
    length_m = Column(Float)
    height_m = Column(Float)
    selected_design_index = Column(Integer)
    design_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrendReport(Base):
    __tablename__ = "trend_reports"

    id = Column(Integer, primary_key=True, index=True)
    room_type = Column(String, index=True)
    report_data = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)
    pick_count = Column(Integer)
