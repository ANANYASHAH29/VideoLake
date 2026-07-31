from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from .database import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    path = Column(Text, nullable=False)
    duration_sec = Column(Float, default=0.0)
    status = Column(String, default="uploaded")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scenes = relationship("Scene", back_populates="video", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="video")


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    start_sec = Column(Float, nullable=False)
    end_sec = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    clip_path = Column(Text, nullable=True)

    diversity = Column(Float, default=0.0)
    novelty = Column(Float, default=0.0)
    caption_alignment = Column(Float, default=0.0)
    motion_complexity = Column(Float, default=0.0)
    visual_quality = Column(Float, default=0.0)
    utility = Column(Float, default=0.0)

    selected = Column(Boolean, default=False)
    cluster_id = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)

    video = relationship("Video", back_populates="scenes")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)
    kind = Column(String, nullable=False)
    status = Column(String, default="pending")
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    video = relationship("Video", back_populates="jobs")
