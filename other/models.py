from datetime import datetime
import asyncio

from sqlalchemy import ForeignKey
from sqlalchemy import MetaData
from sqlalchemy import func
from sqlalchemy import String, Text, DateTime, BigInteger
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "bot_user"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    send_lim: Mapped[int] = mapped_column(default=2)
    find_lim: Mapped[int] = mapped_column(default=6)
    send_amount: Mapped[int] = mapped_column(default=0)
    find_amount: Mapped[int] = mapped_column(default=0)
    receive_amount: Mapped[int] = mapped_column(default=0)
    likes_amount: Mapped[int] = mapped_column(default=0)
    likes: Mapped[int] = mapped_column(default=0)
    rating_place: Mapped[int] = mapped_column(default=0, server_default='0')
    bottles: Mapped[int] = mapped_column(default=0)
    warns: Mapped[int] = mapped_column(default=0, server_default='0')
    is_banned: Mapped[bool] = mapped_column(default=False, server_default='False')
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    bottle_relation = relationship("Bottle", back_populates="user_relation", cascade="all, delete, delete-orphan")


class Bottle(Base):
    __tablename__ = "bottle"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(10), server_default="text")
    file_id: Mapped[str] = mapped_column(Text, server_default="")
    author: Mapped[int] = mapped_column(BigInteger, ForeignKey("bot_user.tg_id", ondelete="CASCADE"))
    views: Mapped[int] = mapped_column(default=0)
    rating: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user_relation = relationship("User", back_populates="bottle_relation")
    viewed_relation = relationship("Viewed", back_populates="bottle_relation", cascade="all, delete, delete-orphan")
    liked_relation = relationship("Liked", back_populates="bottle_relation", cascade="all, delete, delete-orphan")
    answer_relation = relationship("Answer", back_populates="bottle_relation", cascade="all, delete, delete-orphan")


class Answer(Base):
    __tablename__ = "answer"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    bottle: Mapped[int] = mapped_column(ForeignKey("bottle.id", ondelete="CASCADE"))
    author: Mapped[int] = mapped_column(BigInteger, ForeignKey("bot_user.tg_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    bottle_relation = relationship("Bottle", back_populates="answer_relation")


class ReportMsg(Base):
    __tablename__ = "report_msg"
    id: Mapped[int] = mapped_column(primary_key=True)
    msg_id: Mapped[int] = mapped_column(BigInteger)
    chat_id: Mapped[int] = mapped_column(BigInteger)
    report_id: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Viewed(Base):
    __tablename__ = "viewed"
    id: Mapped[int] = mapped_column(primary_key=True)
    person: Mapped[int] = mapped_column(BigInteger, ForeignKey("bot_user.tg_id"))
    bottle: Mapped[int] = mapped_column(ForeignKey("bottle.id", ondelete="CASCADE"))

    bottle_relation = relationship("Bottle", back_populates="viewed_relation")


class Liked(Base):
    __tablename__ = "liked"
    id: Mapped[int] = mapped_column(primary_key=True)
    person: Mapped[int] = mapped_column(BigInteger, ForeignKey("bot_user.tg_id"))
    bottle: Mapped[int] = mapped_column(ForeignKey("bottle.id", ondelete="CASCADE"))

    bottle_relation = relationship("Bottle", back_populates="liked_relation")


class RefLink(Base):
    __tablename__ = "ref_link"
    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    count: Mapped[int] = mapped_column(server_default="0")