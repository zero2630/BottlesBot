from datetime import datetime
import asyncio  # noqa: F401

from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import String, Text, DateTime, BigInteger
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "bot_user"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)  # id пользователя в telegram
    send_lim: Mapped[int] = mapped_column(default=2)  # лимит на отправку посланий(обновляется за промежуток времени)
    find_lim: Mapped[int] = mapped_column(default=6)  # deprecated
    send_amount: Mapped[int] = mapped_column(default=0)  # количество отправленных посланий
    find_amount: Mapped[int] = mapped_column(default=0)  # количество найденных посланий
    receive_amount: Mapped[int] = mapped_column(default=0)  # количество полученных ответов
    likes_amount: Mapped[int] = mapped_column(default=0)  # количество полученных лайков
    likes: Mapped[int] = mapped_column(default=0)  # deprecated
    rating_place: Mapped[int] = mapped_column(default=0, server_default="0")  # место в рейтинге по лайкам
    bottles: Mapped[int] = mapped_column(default=0)  # deprecated
    warns: Mapped[int] = mapped_column(default=0, server_default="0")
    is_banned: Mapped[bool] = mapped_column(default=False, server_default="False")
    p_watch_answ_type: Mapped[str] = mapped_column(String(10), server_default="new")  # параметр: вид отображения ответа на послание
    p_send_rand: Mapped[bool] = mapped_column(String(10), server_default="true")  # параметр: отправка случайного послания раз в день
    p_send_like: Mapped[bool] = mapped_column(String(10), server_default="true")  # параметр: отправление уведомления о лайке
    p_bottle_exists: Mapped[int] = mapped_column(server_default="7")  # параметр: время существования отправленного послания
    p_bad_mode: Mapped[bool] = mapped_column(server_default="false")  # параметр: режим бота
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    bottle_relation = relationship(
        "Bottle", back_populates="user_relation", cascade="all, delete, delete-orphan"
    )


class Bottle(Base):
    __tablename__ = "bottle"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)  # текст послания
    type: Mapped[str] = mapped_column(String(10), server_default="text")  # тип послания (например текст, фото, гиф)
    file_id: Mapped[str] = mapped_column(Text, server_default="")  # id файла который был отправлен (используется при отправке медиа)
    author: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("bot_user.tg_id", ondelete="CASCADE")
    )   # id telegram автора послания
    views: Mapped[int] = mapped_column(default=0)  # количество просмотров
    likes: Mapped[int] = mapped_column(server_default="0")  # количество лайков
    dislikes: Mapped[int] = mapped_column(server_default="0")  # количество дизлайков
    rating: Mapped[int] = mapped_column(default=0)  # рейтинг послания, формируется от лайков, дизлайков, частоты ответов на послание
    is_active: Mapped[bool] = mapped_column(server_default="true")  # активность послания; неактивные послания не показываюстя пользователям
    bad: Mapped[bool] = mapped_column(server_default="false")  # в каком режиме бота находится послание
    related_bottle: Mapped[int] = mapped_column(ForeignKey("bottle.id", ondelete="CASCADE"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user_relation = relationship("User", back_populates="bottle_relation")
    viewed_relation = relationship(
        "Viewed", back_populates="bottle_relation", cascade="all, delete, delete-orphan"
    )
    liked_relation = relationship(
        "Liked", back_populates="bottle_relation", cascade="all, delete, delete-orphan"
    )
    # answer_relation = relationship(
    #     "Answer", back_populates="bottle_relation", cascade="all, delete, delete-orphan"
    # )
    report_relation = relationship(
        "Report", back_populates="bottle_relation", cascade="all, delete, delete-orphan"
    )


# class Answer(Base):
#     __tablename__ = "answer"
#     id: Mapped[int] = mapped_column(primary_key=True)
#     text: Mapped[str] = mapped_column(Text)  # текст ответа
#     bottle: Mapped[int] = mapped_column(ForeignKey("bottle.id", ondelete="CASCADE"))  # id послание на которое ответили
#     author: Mapped[int] = mapped_column(BigInteger, ForeignKey("bot_user.tg_id"))  # telegram id автора ответа
#     created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())  # дата создания
#
#     bottle_relation = relationship("Bottle", back_populates="answer_relation")


class Report(Base):
    __tablename__ = "report_msg"
    id: Mapped[int] = mapped_column(primary_key=True)
    bottle: Mapped[int] = mapped_column(ForeignKey("bottle.id", ondelete="CASCADE"))  # id послания на которое пожаловались
    report_author: Mapped[int] = mapped_column(BigInteger, ForeignKey("bot_user.tg_id"))  # автор жалобы
    is_closed: Mapped[bool] = mapped_column(server_default="false")  # статус жалобы
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    bottle_relation = relationship("Bottle", back_populates="report_relation")


class Viewed(Base):
    __tablename__ = "viewed"
    id: Mapped[int] = mapped_column(primary_key=True)
    person: Mapped[int] = mapped_column(BigInteger, ForeignKey("bot_user.tg_id"))  # telegram id пользователя, просмотревшего послание
    bottle: Mapped[int] = mapped_column(ForeignKey("bottle.id", ondelete="CASCADE"))  # id послания

    bottle_relation = relationship("Bottle", back_populates="viewed_relation")


class Liked(Base):
    __tablename__ = "liked"
    id: Mapped[int] = mapped_column(primary_key=True)
    person: Mapped[int] = mapped_column(BigInteger, ForeignKey("bot_user.tg_id"))  # telegram id пользователя, лайкнувшего послание
    bottle: Mapped[int] = mapped_column(ForeignKey("bottle.id", ondelete="CASCADE"))  # id послания

    bottle_relation = relationship("Bottle", back_populates="liked_relation")


class RefLink(Base):
    __tablename__ = "ref_link"
    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[str] = mapped_column(String(32), unique=True)  # уникальное значение ссылки
    name: Mapped[str] = mapped_column(String(100), unique=True)  # deprecated
    count: Mapped[int] = mapped_column(server_default="0")  # количество перешедших пользователей


class OnlineInfo(Base):
    __tablename__ = "online_info"
    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[int]  # количество пользователей онлайн
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
