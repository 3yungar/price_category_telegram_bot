from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardRemove, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.response_parameters import make_row_keyboard, make_year_keyboard, make_month_keyboard
from calculations_price_category.parse_tariffs import get_tariff_url
from calculations_price_category.payment import get_result_file
import io
import pandas as pd

maximum_power_levels = ['Потребителям с максимальной мощностью менее 670 кВт',
                    'Потребителям с максимальной мощностью от 670 кВт до 10 МВт',
                    'Потребителям с максимальной мощностью не менее 10 МВт']
voltage_levels = ['СН II', 'НН']
months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
              'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
regions = ['Москва', 'Московская область']

router = Router()

class ResponseState(StatesGroup):
    maximum_power_level = State()
    voltage_level = State()
    year = State()
    month = State()
    region = State()
    consumption = State()


# Обработчик первого шага, реагирующий на комманду /start в случае, если у пользователя не устанлен никакой state
@router.message(StateFilter(None), Command('calculate'))
async def cmd_max_level_power(message: Message, state: FSMContext):
    await message.answer(text='Выберите категорию по максимальному уровню мощности', reply_markup=make_row_keyboard(maximum_power_levels))
    # Установка пользователю состояния 'level_max_power'
    await state.set_state(ResponseState.maximum_power_level)


# Хендлер, который ловит один из вариантов из списка maximum_power_levels
@router.message(ResponseState.maximum_power_level, F.text.in_(maximum_power_levels))
async def choose_max_level_power(message: Message, state: FSMContext):
    await state.update_data(max_power_level=message.text)
    await message.answer(text='Теперь выберите уровень напряжения:', reply_markup=make_row_keyboard(voltage_levels))
    # Установка пользователю состояния 'voltage_level'
    await state.set_state(ResponseState.voltage_level)


# В случае, если пользователь ввел вручную несуществующую категорию по мощности
@router.message(ResponseState.maximum_power_level)
async def max_power_level_is_incorrectly(message: Message):
    await message.answer(text='Введена неверная категория.\nПожалуйста, выберите одно из названий из списка ниже:', reply_markup=make_row_keyboard(maximum_power_levels))
    

# Хендлер, который ловит один из вариантов из списка voltage_levels
@router.message(ResponseState.voltage_level, F.text.in_(voltage_levels))
async def choose_voltage_level(message: Message, state: FSMContext):
    await state.update_data(voltage_level=message.text)
    await message.answer(text=f'Теперь выберите год', reply_markup=make_year_keyboard())
    # Установка пользователю состояния 'year'
    await state.set_state(ResponseState.year)


# В случае, если пользователь ввел вручную несуществующий уровень мощности
@router.message(ResponseState.maximum_power_level)
async def max_power_level_is_incorrectly(message: Message):
    await message.answer(text='Введен неверный уровень напряжения.\nПожалуйста, выберите одно из названий из списка ниже:', reply_markup=make_row_keyboard(voltage_levels))
    

# Хендлер, который ловит год
@router.message(ResponseState.year, F.text)
async def choose_year(message: Message, state: FSMContext):
    await state.update_data(year=message.text)
    await message.answer(text=f'Теперь выберите месяц', reply_markup=make_month_keyboard())
    # Установка состояния месяц
    await state.set_state(ResponseState.month)


# Хендлер, который ловит месяц
@router.message(ResponseState.month, F.text)
async def choose_month(message: Message, state: FSMContext):
    # Словарь с параметрами запроса
    user_data = await state.get_data()

    month = str(months.index(message.text) + 1).rjust(2, '0')
    period = user_data['year'] + '-' + month

    url = get_tariff_url(user_data['max_power_level'], period)
    # Проверка на существование ссылки на файл с тарифами
    if url is None:
        await message.answer(text='На сайте https://www.mosenergosbyt.ru/legals/tariffs-n-prices/ для выбранного периода еще не выставлены тарифы')
    else:
        await state.update_data(month=month, period=period)
        await message.answer(text='Теперь выберите регион', reply_markup=make_row_keyboard(regions))
        await state.set_state(ResponseState.region)


# Хендлер, который ловит регион
@router.message(ResponseState.region)
async def choose_region(message: Message, state: FSMContext):
    await state.update_data(region=message.text)
    await message.answer(text='Подгрузите файл .xlsx с двумя столбцами: ["time", "consumption"]', reply_markup=ReplyKeyboardRemove())
    await state.set_state(ResponseState.consumption)


# Хендлер, который принимает эксель файл с потреблением
@router.message(ResponseState.consumption)
async def get_consumption(message: Message, state: FSMContext):
    file_id = message.document.file_id
    file = await message.bot.get_file(file_id)
    file_path = file.file_path
    my_object = io.BytesIO()
    
    # Представление в байтовом виде эксель файла, отправленного пользователем
    consumption_file = await message.bot.download_file(file_path, my_object)

    # расчет ценовых категорий
    user_data = await state.get_data()
    output_file = get_result_file(consumption_file, 
                                user_data['max_power_level'], 
                                user_data['voltage_level'], 
                                user_data['period'], 
                                user_data['region'])
    
    if output_file == 'LenghtError':
        await message.answer(text='Некорректная форма данных. Подгрузите корректный файл')
    elif output_file == 'periodError':
        await message.answer(text='Данные о потреблении относятся к другому периоду. Подгрузите корректный файл')
    else:
        await message.answer(text='Ценовые категории')
        await state.clear()
        await message.answer_document(document=BufferedInputFile(file=output_file, filename=user_data['period'] + '.xlsx'))