from math import ceil
from aiogram.types import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButtonRequestUser, KeyboardButtonPollType, KeyboardButtonRequestChat
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from sqlalchemy.ext.asyncio import AsyncSession  # Импорт AsyncSession для работы с базой данных
from sqlalchemy import select
from models import Birthdays
from sqlalchemy.ext.asyncio import async_sessionmaker

from tasks import Session


start = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text="Добавить день рождение"), KeyboardButton(text="Показать дни раждения")
        ]
    ], resize_keyboard=True, one_time_keyboard=True)

async def get_username_id():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Отправить id именинника", request_user=KeyboardButtonRequestUser(request_id=1)), KeyboardButton(text='Отмена'))
    return builder.as_markup(resize_keyboard=True)


async def select_allusers(session: AsyncSession, user_id):
    query = select(Birthdays).where(Birthdays.user_id == user_id)  # Предположим, что ваша модель пользователей называется "User"
    result = await session.execute(query)  # Выполнение запроса к базе данных
    users = result.scalars().all()  # Получение списка пользователей
    return users  # Возвращение списка пользователей


async def set_notif_date():
    builder = InlineKeyboardBuilder()
    builder.button(text="Установить дату", callback_data="set_date")
    builder.button(text="Установить уведомление", callback_data="set_notif")
    builder.button(text="Отменить", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


class Pagination(CallbackData, prefix="pag"):
    action: str  # Действие
    page: int  # Номер страницы

# Функция для создания клавиатуры с пользователями и кнопками для перелистывания
async def paginator(session: AsyncSession, page: int = 0, limit: int = 5, user_id=0):
    users = await select_allusers(session=session, user_id=user_id)  # Получение списка пользователей
    builder = InlineKeyboardBuilder()  # Создание объекта InlineKeyboardBuilder
    start_offset = page * limit  # Вычисление начального смещения на основе номера страницы
    end_offset = start_offset + limit  # Вычисление конечного смещения

    for user in users[start_offset:end_offset]:  # Перебор пользователей для текущей страницы
        builder.row(InlineKeyboardButton(text=f'👤 {user.full_name}', callback_data=BirthdayCallback(action='get', id=user.birthday_boy_id).pack()))  # Добавление кнопки для каждого пользователя
    buttons_row = []  # Создание списка кнопок
    if page > 0:  # Проверка, что страница не первая
        buttons_row.append(InlineKeyboardButton(text="⬅️", callback_data=Pagination(action="prev", page=page - 1).pack()))  # Добавление кнопки "назад"
    if end_offset < len(users):  # Проверка, что ещё есть пользователи для следующей страницы
        buttons_row.append(InlineKeyboardButton(text="➡️", callback_data=Pagination(action="next", page=page + 1).pack()))  # Добавление кнопки "вперед"
    elif limit < len(users):  # Если пользователи закончились
        buttons_row.append(InlineKeyboardButton(text="➡️", callback_data=Pagination(action="next", page=0).pack()))  # Возвращение на первую страницу
    builder.row(*buttons_row)  # Добавление кнопок навигации
    builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='cancel'))  # Добавление кнопки "назад"
    return builder.as_markup()  # Возвращение клавиатуры в виде разметки


class Edit(CallbackData, prefix='edit'):
    action: str
    user_id: int


async def edit(user_id):
    button = InlineKeyboardBuilder()
    button.add(InlineKeyboardButton(text='Изменить имя', callback_data=Edit(action='edit_name', user_id=user_id).pack()))
    button.row(InlineKeyboardButton(text='Изменить дату рождения', callback_data=Edit(action='edit_birth', user_id=user_id).pack()), 
               InlineKeyboardButton(text="Изменить дату уведомления", callback_data=Edit(action='edit_notif', user_id=user_id).pack()))
    button.row(InlineKeyboardButton(text='Удалить', callback_data=Edit(action='delete', user_id=user_id).pack()))
    return button.as_markup()



async def universal_keyboard(buttons: dict=None):
    '''
    request_users
    request_chat
    request_contact
    request_location
    request_poll
    '''
    if buttons is None:
        return 0
    
    builder = ReplyKeyboardBuilder()

    for button, property in buttons.items():
        match property:
            case 'request_users':
                builder.button(text=button, request_user=KeyboardButtonRequestUser(request_id=1))
            case 'request_chat':
                builder.button(text=button, request_chat=KeyboardButtonRequestChat(request_id=1))

            case 'request_contact':
                builder.button(text=button, request_contact=True)

            case 'request_location':
                builder.button(text=button, request_location=True)

            case 'request_poll':
                builder.button(text=button, request_poll=KeyboardButtonPollType(type='regular'))


class BirthdayCallback(CallbackData, prefix='birthday'):
    action: str
    id: int
