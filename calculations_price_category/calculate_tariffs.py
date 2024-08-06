import numpy as np
import pandas as pd
from calculations_price_category.parse_tariffs import get_tariff_excel_file


months = {
    '01': ['январь', 31],
    '02': ['февраль', 28],
    '03': ['март', 31],
    '04': ['апрель', 30],
    '05': ['май', 31],
    '06': ['июнь', 30],
    '07': ['июль', 31],
    '08': ['август', 31],
    '09': ['сентябрь', 30],
    '10': ['октябрь', 31],
    '11': ['ноябрь', 30],
    '12': ['декабрь', 31]
}


def calculate_tariffs(maximum_power_level, voltage_level, period, region):
    '''
    Возвращает значения тарифов для 1, 3, 4 ценовых категорий
    '''
    year, month = period.split('-')
    if int(year) in [x for x in range(2000, 2100, 4)]:
        months['02'][1] += 1


    tariff_xl = get_tariff_excel_file(maximum_power_level, period)

    # Данные о тарифах по категориям
    r = 'М' if region == 'Москва' else 'О'
    get_sheet_name = lambda x: f'{r}_{months[month][0]} {x} цк'

    sheet_pc1 = tariff_xl.parse(
        get_sheet_name(1), 
        names=['number', 'group', 'ВН', 'СН I', 'СН II', 'НН'], 
        skiprows=12
        ).loc[0]

    sheet_pc3 = tariff_xl.parse(get_sheet_name(3))
    sheet_pc4 = tariff_xl.parse(get_sheet_name(4))

    # Тариф за 1 кВтч/руб по первой ценовой категории
    consumption_rate_pc1 = sheet_pc1[voltage_level] / 1000

    # Тариф пиковой мощности 1 кВт/руб для 3 и 4 ценовых категорий 
    power_rate_df = sheet_pc4[sheet_pc4['Unnamed: 0'] == '- средневзвешенная нерегулируемая цена на мощность на оптовом рынке'].dropna(axis=1).copy()
    peak_power_rate = float(power_rate_df.values[0][-1].replace(',', '.')) / 1000

    # Тариф по передаваемой транспортной мощности 1 кВт/руб для 4 ценовой категории
    transport_rate_df = sheet_pc4[sheet_pc4['Unnamed: 0'] == 'Иные прочие потребители'].dropna(axis=1).copy()
    transport_rate_df.columns = ['category', 'ВН', 'СН I', 'СН II', 'НН']
    transport_power_rate = transport_rate_df.iloc[0][voltage_level] / 1000


    def get_rate_matrix(sheet_category, voltage_level):
        description = 'Ставка для фактических почасовых объемов покупки электрической энергии, отпущенных на уровне напряжения ' + voltage_level

        # Убираем строки, где значение первого столбца не относится к классу int или не равно 'Дата'
        price_category = sheet_category[
        (sheet_category['Unnamed: 0'] == 'Дата') | 
        (sheet_category['Unnamed: 0'].apply(lambda x: isinstance(x, int)))
        ].copy(deep=True)
    
        # Заменяем латинские заглавные буквы на кириллицу в описании матриц тарифов (уровни напряжения СН II и НН)
        from_eng_to_rus = lambda x: x.replace('C', 'С').replace('H', 'Н')
        description_mask = price_category['Unnamed: 0'] == 'Дата'
        price_category.loc[description_mask, 'Unnamed: 1'] = price_category.loc[description_mask, 'Unnamed: 1'].apply(from_eng_to_rus)

        # Отрезаем датафрейм по описанию и количеству дней в месяце
        start_index = price_category[price_category['Unnamed: 1'].apply(lambda x: type(x) == str and x == description)].index[0]
        rate_matrix = price_category.loc[start_index:].head(months[month][1] + 1)

        rate_matrix.index = rate_matrix['Unnamed: 0']
        rate_matrix = rate_matrix.dropna().drop(columns='Unnamed: 0')
        rate_matrix.columns = np.arange(1, 25)
        rate_matrix = rate_matrix.replace('\,', '.', regex=True).astype('float')
        return rate_matrix / 1000

    pc3_rate_matrix = get_rate_matrix(sheet_pc3, voltage_level)
    pc4_rate_matrix = get_rate_matrix(sheet_pc4, voltage_level)

    return consumption_rate_pc1, peak_power_rate, transport_power_rate, pc3_rate_matrix, pc4_rate_matrix
