import textwrap
from passwords.models import Password
from structured_functions.passwords import send_password_menu, send_create_password_send_site, send_create_password_send_site_alias, send_create_password_generate_password, send_create_password_regenerate_password, send_remember_password_by_site_alias, send_remember_password_by_site, send_remember_password_by_choice, send_remember_password_success, send_remember_password_error, feed_shkontik, send_create_password_good_password
from django.core.management.base import BaseCommand
from telegram.ext import CommandHandler, ConversationHandler, Filters, MessageHandler, Updater, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup
import logging
from django.conf import settings
from enum import Enum, auto, unique
from logger import ChatbotLogsHandler
from django.core.validators import URLValidator, ValidationError
from urllib.parse import urlparse

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


def start(update, context):

    text = textwrap.dedent(
        """
        Привет, меня зовут *Шконтик*, и я здесь главный!!!
        """
    )

    keyboard = [
        ['🔧 Пароли']
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

    elif hasattr(query, 'data'):

        if 'feed' == query.data:
            feed_shkontik(update, context)


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


class Command(BaseCommand):
    help = 'Телеграм-бот, снимающий омографию'

    def handle(self, *args, **options):
        telegram_token = settings.TELEGRAM_TOKEN
        telegram_chat_id = settings.TELEGRAM_CHAT_ID

        logging.basicConfig(level=logging.WARNING)
        logger.addHandler(ChatbotLogsHandler(telegram_chat_id, telegram_token))

        updater = Updater(telegram_token)
        dispatcher = updater.dispatcher

        menu_message_handler = MessageHandler(Filters.regex('🔧 Пароли'), handle_menu)
        menu_callback_handler = CallbackQueryHandler(handle_menu, pattern='feed')

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
                ]
            },
            fallbacks=[],
            allow_reentry=True,
            name='bot_conversation'
        )

        dispatcher.add_handler(conv_handler)

        updater.start_polling()
        updater.idle()
