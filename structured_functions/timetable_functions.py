import textwrap
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def send_timetable_menu(update, context):

    text = textwrap.dedent(
        """Ну хорошо, деловая колбаса, давай разберемся с твоим расписанием :))"""
    )

    keyboard = [
        [InlineKeyboardButton('Я хочу добавить событие', callback_data='create')],
        [InlineKeyboardButton('Покажи календарь', callback_data='show')]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text=text, reply_markup=markup)


def send_timetable_good_date(update, context):

    text = textwrap.dedent(
        """Я рад што оказался тебе полезен, но теперь я требую гречневовый йогурт!!!!"""
    )
    keyboard = [
        [InlineKeyboardButton('Покормить греческим йогуртом', callback_data='feed')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query = update.callback_query
    context.bot.edit_message_text(text=text, reply_markup=reply_markup, message_id=query.message.message_id,
                                  chat_id=query.message.chat_id)


def send_timetable_bad_date(update, context):
    query = update.message

    text = 'ЫЫЫЫЫ, ну и пожалуйста. Отправяй еще раз в формате DD.MM.YYYY mm:hh, и я подумаю буду добавлять или нет'

    context.bot.edit_message_text(text=text, chat_id=query.message.chat_id, message_id=query.message.message_id)
