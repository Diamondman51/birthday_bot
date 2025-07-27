from datetime import datetime
from enum import Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Integer, String, Enum as SQEnum


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=True, unique=True)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    birthdays: Mapped[list['Birthdays']] = relationship(back_populates='user', cascade='all, delete')
    groups: Mapped[list['Groups']] = relationship(back_populates='user', cascade='all, delete')

    def __repr__(self):
        return f"User(id={self.id!r}, username={self.username!r}, full_name={self.full_name!r})"


class Langs(str, Enum):
    ru = 'ru'
    en = 'en'
    uz = 'uz'


class Birthdays(Base):
    __tablename__ = 'birthdays'
    id: Mapped[int] = mapped_column(Integer, unique=True, autoincrement=True, nullable=False, primary_key=True)
    full_name: Mapped[str] = mapped_column(String, unique=False, nullable=True)
    birthday_boy_username: Mapped[str] = mapped_column(String, unique=False, nullable=True)
    notification_time: Mapped[datetime] = mapped_column(DateTime, unique=False, nullable=True)
    birthday_boy_id: Mapped[int] = mapped_column(Integer, unique=False, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id'), nullable=True)
    user: Mapped[User] = relationship(back_populates='birthdays')
    group: Mapped['Groups'] = relationship(back_populates='birthdays')
    lang: Mapped['Langs'] = mapped_column(SQEnum(Langs), nullable=True)
    desc: Mapped[str] = mapped_column(String(255), nullable=True)

    def __repr__(self):
        return f"Birthdays({self.birthday_boy_username=!r}, {self.full_name=!r}, {self.notification_time=!r}, {self.birthday_boy_id=!r}, {self.date=!r})"


class Groups(Base):
    __tablename__ = 'groups'
    id: Mapped[int] = mapped_column(Integer, unique=True, autoincrement=True, nullable=False, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=False, nullable=True)
    group_id: Mapped[int] = mapped_column(Integer, unique=False, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    birthdays: Mapped[list[Birthdays]] = relationship(back_populates='group')
    user: Mapped[User] = relationship(back_populates='groups')
    