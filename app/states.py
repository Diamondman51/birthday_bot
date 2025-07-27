from aiogram.fsm.state import State, StatesGroup


class BirthdayState(StatesGroup):
    birthday_boy_username = State()
    birthday_boy_id = State()
    notification_time = State()
    date = State()
    group_id = State()
    send_username_or_id = State()
    full_name = State()
    desc = State()
    lang = State()
    time__ = State()


class EditState(StatesGroup):
    user_id = State()
    name = State()
    birth = State()
    notif = State()


class AddGroupState(StatesGroup):
    group_id = State()
    name = State()
    user_id = State()
    birthdays = State()

