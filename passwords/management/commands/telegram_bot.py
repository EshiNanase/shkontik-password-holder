import textwrap
from passwords.models import Password
from structured_functions.passwords import send_password_menu, send_create_password_send_site, send_create_password_send_site_alias, send_create_password_generate_password, send_create_password_regenerate_password, send_remember_password_by_site_alias, send_remember_password_by_site, send_remember_password_by_choice, send_remember_password_success, send_remember_password_error, feed_shkontik, send_create_password_good_password
from structured_functions.timetable_functions import send_timetable_menu, send_timetable_good_date, send_timetable_bad_date
from django.core.management.base import BaseCommand
from telegram.ext import CommandHandler, ConversationHandler, Filters, MessageHandler, Updater, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import logging
from django.conf import settings
from enum import Enum, auto, unique
from logger import ChatbotLogsHandler
from django.core.validators import URLValidator, ValidationError
from urllib.parse import urlparse
from collections import defaultdict
from datetime import datetime
from django.utils import dateformat
from timetable.models import Event

logger = logging.getLogger(__file__)
validator = URLValidator()


@unique
class States(Enum):
    Menu = auto()

    Password = auto()

    # CREATE_PASSWORD
    Password_Create_Site = auto()
    Password_Create_Site_Alias = auto()
    Password_Create_Generate_Password = auto()

    # REMEMBER_PASSWORD
    Password_Remember_Site = auto()
    Password_Remember_Site_Alias = auto()

    Timetable = auto()

    # CREATE EVENT
    Timetable_Create_Event = auto()
    Timetable_Create_Event_Title = auto()
    Timetable_Create_Event_Description = auto()
    Timetable_Create_Event_Confirmation = auto()

    Timetable_Show_Events = auto()


def start(update, context):

    text = textwrap.dedent(
        """
        Привет, меня зовут *Шконтик*, и я здесь главный!!!
        """
    )

    keyboard = [
        ['🔧 Пароли'],
        ['📅 Расписание']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')

    return States.Menu


def handle_menu(update, context):

    message = update.message
    query = update.callback_query

    if hasattr(message, 'text'):

        if '🔧 Пароли' == message.text:
            send_password_menu(update, context)
            return States.Password

        elif '📅 Расписание' == message.text:
            send_timetable_menu(update, context)
            return States.Timetable

    elif hasattr(query, 'data'):

        if 'feed' == query.data:
            feed_shkontik(update, context)

        elif 'timetable' in query.data:

            if 'delete' in query.data:
                event_id = query.data.split('#')[-1]
                context.user_data['event_to_delete'] = Event.objects.get(id=event_id)
                keyboard = [
                    [InlineKeyboardButton('Покормить', callback_data='feed')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                context.bot.edit_message_text(text='Уверен?? Если да, то корми йогуртом лох', reply_markup=reply_markup, chat_id=query.message.chat_id, message_id=query.message.message_id)


def handle_passwords_menu(update, context):

    query = update.callback_query

    if 'password#new' == query.data:
        send_create_password_send_site(update, context)
        return States.Password_Create_Site

    elif 'password#old' in query.data:

        if 'choice' in query.data:
            send_remember_password_by_choice(update, context)

        elif 'site_url' in query.data:
            send_remember_password_by_site(update, context)
            return States.Password_Remember_Site

        elif 'site_alias' in query.data:
            send_remember_password_by_site_alias(update, context)
            return States.Password_Remember_Site_Alias


def handle_passwords_send_site(update, context):

    message = update.message.text

    try:
        validator(message)
        site = urlparse(message).netloc

        if Password.objects.filter(user_id=update.message.chat_id, site=site):
            update.message.reply_text('У меня уже записан один такой сайт...')

        context.user_data['create_password'] = {}
        context.user_data['create_password']['site'] = site

        send_create_password_send_site_alias(update, context)
        return States.Password_Create_Site_Alias

    except ValidationError:
        update.message.reply_text('Эй, врун, это не сайт :((')


def handle_passwords_send_site_alias(update, context):

    message = update.message.text

    if Password.objects.filter(user_id=update.message.chat_id, site_alias=message):
        update.message.reply_text('У меня уже записан один такой сайт...')

    context.user_data['create_password']['site_alias'] = message
    send_create_password_generate_password(update, context)
    return States.Password_Create_Generate_Password


def handle_passwords_generate_password(update, context):

    query = update.callback_query

    if 'good_password' == query.data:

        site = context.user_data['create_password']['site']
        site_alias = context.user_data['create_password']['site_alias']
        password = context.user_data['create_password']['password']

        Password.objects.create(
            user_id=query.message.chat_id,
            site=site,
            site_alias=site_alias,
            password=password
        )

        send_create_password_good_password(update, context)
        return States.Menu

    elif 'bad_password' == query.data:
        send_create_password_regenerate_password(update, context)


def handle_remember_password_by_site(update, context):

    message = update.message.text

    site = urlparse(message).netloc
    password = Password.objects.filter(
        user_id=update.message.chat_id,
        site=site
    )

    if password:
        send_remember_password_success(update, context, password.first())
        return States.Menu

    else:
        send_remember_password_error(update, context)


def handle_remember_password_by_site_alias(update, context):

    message = update.message.text

    password = Password.objects.filter(
        user_id=update.message.chat_id,
        site_alias=message
    )

    if password:
        send_remember_password_success(update, context, password.first())
        return States.Menu

    else:
        send_remember_password_error(update, context)


def handle_timetable(update, context):

    query = update.callback_query

    if 'create' == query.data:
        text = textwrap.dedent(
            """
            Ого, оказывается у тебя что-то в жизни интересное есть!
            Шучу шучу хихих, отправляй дату в формате DD.MM.YYYY hh:mm и добавим все
            """
        )
        context.bot.edit_message_text(text=text, chat_id=query.message.chat_id, message_id=query.message.message_id)
        return States.Timetable_Create_Event

    elif 'show' == query.data:
        text = textwrap.dedent(
            """
            Ну ща посмотрим, че там у тебя по делишечкам хех. Отправь дату в формате DD.MM.YYYY и поглядим
            """
        )
        context.bot.edit_message_text(text=text, chat_id=query.message.chat_id, message_id=query.message.message_id)
        return States.Timetable_Show_Events


def handle_timetable_show_events(update, context):

    message = update.message
    date = datetime.strptime(message.text, "%d.%m.%Y")

    events = Event.objects.filter(at__year=date.year, at__month=date.month, at__day=date.day).order_by('-at__hour')

    for event in events:
        text = textwrap.dedent(
            f"""
            ⏱ *{event.title.upper()}* - {event.at.strftime('%H:%M')}
            {event.description}
            """
        )
        keyboard = [
            [InlineKeyboardButton('Удалить', callback_data=f'timetable#delete#{event.id}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')

    if not events:
        update.message.reply_text(text='Кажется, делишек у тебя нету. Отдыхаешь!!!')


def handle_timetable_event_creation_date(update, context):

    message = update.message

    context.user_data['timetable'] = defaultdict(dict)
    context.user_data['timetable']['event']['date'] = datetime.strptime(message.text, "%d.%m.%Y %H:%M")

    text = textwrap.dedent(
        """
        Ничего себе, надеюсь сам не забуду!!!
        Как хочешь назвать событие??
        """
    )
    update.message.reply_text(text=text)
    return States.Timetable_Create_Event_Title


def handle_timetable_event_creation_title(update, context):

    message = update.message

    context.user_data['timetable']['event']['title'] = message.text

    text = textwrap.dedent(
        """
        А по-интереснее придумать не? Лана пиши описание события
        """
    )
    update.message.reply_text(text=text)
    return States.Timetable_Create_Event_Description


def handle_timetable_event_creation_description(update, context):

    message = update.message

    context.user_data['timetable']['event']['description'] = message.text

    text = textwrap.dedent(
        f"""
        Давай теперь убедимся, все ли я правильно понял!

        ⏱ *{context.user_data['timetable']['event']['title'].upper()}*
        {dateformat.format(context.user_data['timetable']['event']['date'], 'd E Y H:i')}
        {context.user_data['timetable']['event']['description']}
        """
    )

    keyboard = [
        [InlineKeyboardButton('Правильно', callback_data='good')],
        [InlineKeyboardButton('Давай заново', callback_data='bad')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
    return States.Timetable_Create_Event_Confirmation


def handle_timetable_event_creation_confirmation(update, context):

    query = update.callback_query

    if 'good' == query.data:
        Event.objects.create(
            user_id=query.message.chat_id,
            at=context.user_data['timetable']['event']['date'],
            title=context.user_data['timetable']['event']['title'],
            description=context.user_data['timetable']['event']['description']
        )
        send_timetable_good_date(update, context)
        return States.Menu

    elif 'bad' == query.data:
        send_timetable_bad_date(update, context)
        return States.Timetable_Create_Event


class Command(BaseCommand):
    help = 'Телеграм-бот, снимающий омографию'

    def handle(self, *args, **options):
        telegram_token = settings.TELEGRAM_TOKEN
        telegram_chat_id = settings.TELEGRAM_CHAT_ID

        logging.basicConfig(level=logging.WARNING)
        logger.addHandler(ChatbotLogsHandler(telegram_chat_id, telegram_token))

        updater = Updater(telegram_token)
        dispatcher = updater.dispatcher

        menu_message_handler = MessageHandler(Filters.regex('🔧 Пароли|📅 Расписание'), handle_menu)
        menu_callback_handler = CallbackQueryHandler(handle_menu, pattern='feed|timetable*')

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                States.Menu: [
                    menu_message_handler,
                    menu_callback_handler,
                ],
                States.Password: [
                    menu_message_handler,
                    menu_callback_handler,
                    CallbackQueryHandler(handle_passwords_menu)
                ],
                States.Password_Create_Site: [
                    menu_message_handler,
                    menu_callback_handler,
                    MessageHandler(Filters.text, handle_passwords_send_site)
                ],
                States.Password_Create_Site_Alias: [
                    menu_message_handler,
                    menu_callback_handler,
                    MessageHandler(Filters.text, handle_passwords_send_site_alias)
                ],
                States.Password_Create_Generate_Password: [
                    menu_message_handler,
                    menu_callback_handler,
                    CallbackQueryHandler(handle_passwords_generate_password)
                ],
                States.Password_Remember_Site: [
                    menu_message_handler,
                    menu_callback_handler,
                    MessageHandler(Filters.text, handle_remember_password_by_site)
                ],
                States.Password_Remember_Site_Alias: [
                    menu_message_handler,
                    menu_callback_handler,
                    MessageHandler(Filters.text, handle_remember_password_by_site_alias)
                ],
                States.Timetable: [
                    menu_message_handler,
                    menu_callback_handler,
                    CallbackQueryHandler(handle_timetable)
                ],
                States.Timetable_Create_Event: [
                    menu_message_handler,
                    menu_callback_handler,
                    MessageHandler(Filters.text, handle_timetable_event_creation_date)
                ],
                States.Timetable_Create_Event_Title: [
                    menu_message_handler,
                    menu_callback_handler,
                    MessageHandler(Filters.text, handle_timetable_event_creation_title)
                ],
                States.Timetable_Create_Event_Description: [
                    menu_message_handler,
                    menu_callback_handler,
                    MessageHandler(Filters.text, handle_timetable_event_creation_description)
                ],
                States.Timetable_Create_Event_Confirmation: [
                    menu_message_handler,
                    menu_callback_handler,
                    CallbackQueryHandler(handle_timetable_event_creation_confirmation)
                ],
                States.Timetable_Show_Events: [
                    menu_message_handler,
                    menu_callback_handler,
                    MessageHandler(Filters.text, handle_timetable_show_events)
                ]
            },
            fallbacks=[],
            allow_reentry=True,
            name='bot_conversation'
        )

        dispatcher.add_handler(conv_handler)

        updater.start_polling()
        updater.idle()
