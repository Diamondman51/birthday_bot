from aiogram import F, Router
from aiogram.filters import CommandStart

from handlers import *

def setup():
    router = Router()
    router.message.register(start, CommandStart())
    router.message.register(add_birthday, F.text == "Добавить день рождение")
    router.message.register(get_full_name, BirthdayState.full_name)
    router.callback_query.register(get_date, F.data == "set_date")
    router.callback_query.register(get_notif, F.data == "set_notif")
    router.callback_query.register(cancel, F.data == "cancel")
    router.message.register(cancel_t, F.text.lower() == "отмена")
    router.message.register(username_or_id, BirthdayState.send_username_or_id)
    router.message.register(set_date, BirthdayState.date)
    router.message.register(set_notif, BirthdayState.notification_time)
    router.message.register(show_birthdays, F.text == "Показать дни раждения")
    router.callback_query.register(show_birthday, BirthdayCallback.filter(F.action == "get"))
    router.callback_query.register(pagination_handler, Pagination.filter())
    router.callback_query.register(edit_name, Edit.filter(F.action == 'edit_name'))
    router.message.register(get_edited_name, EditState.name)
    router.callback_query.register(delete_birth, Edit.filter(F.action == 'delete'))
    router.callback_query.register(edit_birth, Edit.filter(F.action == 'edit_birth'))
    router.message.register(get_edited_birth, EditState.birth)
    router.callback_query.register(edit_notif, Edit.filter(F.action == 'edit_notif'))
    router.message.register(get_edited_notif, EditState.notif)

    return router
