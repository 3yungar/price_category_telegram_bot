import datetime as dt
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def make_row_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    '''
    Создает реплай-клавиатуру с кнопками в один столбец
    :param items: список текстов для кнопок
    :return: объект реплай-клавиатуры
    '''

    keyboard = [[KeyboardButton(text=item)] for item in items]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def make_year_keyboard() -> ReplyKeyboardMarkup:
    '''
    Создает реплай-клавиатуру с кнопками для выбора года
    '''
    year = dt.datetime.today().year
    keyboard = [[KeyboardButton(text=str(x)) for x in range(year - 3, year + 1)]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def make_month_keyboard() -> ReplyKeyboardMarkup:
    '''
    Создает реплай-клавиатуру с кнопками для выбора месяца
    '''
    months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
              'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    keyboard = []
    indx = 0
    for _ in range(3):
        row = []
        for _ in range(4):
            row.append(KeyboardButton(text=months[indx]))
            indx += 1
        keyboard.append(row)

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def make_start_keyboard() -> ReplyKeyboardMarkup:
    '''
    Создает реплай-клавиатуру для стартового меню
    '''
    keyboard = [[KeyboardButton('/calculate')]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
