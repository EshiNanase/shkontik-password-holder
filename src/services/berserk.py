from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import textwrap
from berserk.models import TableLink
import gspread as gc

GC = gc.service_account(filename='cred.json')


def berserk_add_card(user_id, worksheet_index, card_index, foil):
    table_link_obj = TableLink.objects.filter(user_id=user_id).first()
    table = GC.open_by_url(table_link_obj.link)
    sheets = table.worksheets()[2:]
    worksheet = sheets[int(worksheet_index)]

    records = worksheet.get_all_records()
    for record in records:
        if record['Номер'] == int(card_index):
            break
    else:
        return False, 'Не получилось. Кажется, ты ошибся с айди карты'

    cell = worksheet.find(record['Название'])

    if foil:
        cell_to_be_updated_column = cell.col + 4
    else:
        cell_to_be_updated_column = cell.col + 3

    cell_value = worksheet.cell(cell.row, cell_to_be_updated_column).value
    if cell_value is None:
        return False, 'Не получилось. Кажется, в этом сете нет фойловых или ты ошибся с айди карты'

    worksheet.update_cell(cell.row, cell_to_be_updated_column, int(cell_value) + 1)
    return True, {'name': record['Название'], 'quantity': int(cell_value) + 1}


def send_berserk_menu(update, context):
    text = textwrap.dedent(
        """
        Русы бьются за Лаар?? Надеюсь у тебя появились друзья, чтобы зарубиться с ними. Че хочешь то, а??
        """
    )

    keyboard = [
        [InlineKeyboardButton('Я хочу добавить новую карту в коллекцию', callback_data='berserk#add_card')],
        [InlineKeyboardButton('Я хочу поменять ссылку на таблицу', callback_data='berserk#change_table')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')


def send_berserk_add_card_choose_set(update, context):

    query = update.callback_query

    text = textwrap.dedent(
        """
        Признавайся, какой твой любимый сет? Надеюсь не учебный хаха. Лана, выбери сет, в который хочешь добавить карту
        """
    )
    table_link_obj = TableLink.objects.filter(user_id=query.message.chat_id).first()
    table = GC.open_by_url(table_link_obj.link)
    sheets = table.worksheets()[2:]

    keyboard = [[InlineKeyboardButton(f'{sheet.title}', callback_data=f'#berserk#add_card#{ind}')] for ind, sheet in enumerate(sheets)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.edit_message_text(text=text, message_id=query.message.message_id, chat_id=query.message.chat_id, reply_markup=reply_markup)


def send_berserk_add_card_foil(update, context):

    query = update.callback_query
    text = textwrap.dedent(
        """
        А мне этот сет не нраица... Ну лан, скажи теперь, фойл это или нет. Отправь "да" или "нет"
        """
    )
    context.bot.edit_message_text(text=text, message_id=query.message.message_id, chat_id=query.message.chat_id)
    worksheet_index = query.data.split('#')[-1]
    context.user_data['berserk_add_worksheet_index'] = worksheet_index


def send_berserk_add_card_add_first_card(update, context):

    if 'да' in update.message.text:
        context.user_data['foil'] = True
    else:
        context.user_data['foil'] = False

    text = textwrap.dedent(
        """
        Эх вот би фойл королеву мертвых, да? Ну лан, отправь теперь ID карты, которую хочешь добавить
        """
    )
    update.message.reply_text(text=text)


# TODO: не добавлять карту в таблицу, а добавлять в словарь и потом его отдавать целиком
def send_berserk_add_card_loop(update, context):

    try:
        success, message = berserk_add_card(update.message.chat_id, context.user_data['berserk_add_worksheet_index'], update.message.text, context.user_data['foil'])
        if success:
            info = f'Ты добавил {"фойл " if context.user_data["foil"] else ""}{message["name"]} - {message["quantity"]}\nОтправляй дальше или напиши "хватит" :)'
            update.message.reply_text(text=info, parse_mode='Markdown')
        else:
            update.message.reply_text(text=message)
    except gc.exceptions.APIError:
        update.message.reply_text(text='Впали в загрузку. Приходи попозже(')


def send_berserk_change_table_change_table(update, context):
    pass


def send_berserk_change_table_result(update, context):
    pass
