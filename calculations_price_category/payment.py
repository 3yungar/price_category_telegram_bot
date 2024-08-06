import io
import pandas as pd
from openpyxl.styles import Alignment
from calculations_price_category.parse_peak_transport_hours import parse_hours
from calculations_price_category.calculate_tariffs import calculate_tariffs


def transform_from_df_to_matrix(consumption_df):
    '''
    Преобразует временной ряд с потреблением в матрицу день/час потребления 
    '''
    df = consumption_df.copy()
    df['day'] = df['time'].dt.day
    df['hour'] = df['time'].dt.hour
    df = df.pivot(index='day', columns='hour', values='total')
    
    return df

def get_result_file(file, maximum_power_level, voltage_level, period, region):
    # Выгружаем данные о тарифах
    consumption_rate_pc1, peak_power_rate, transport_power_rate, pc3_rate_matrix, pc4_rate_matrix = calculate_tariffs(maximum_power_level, voltage_level, period, region)
    peak_power_df, transport_power_df = parse_hours(period)
    
    year, month = period.split('-')
    correct_shape = pc3_rate_matrix.shape

    # Датафрейм с потреблением
    consumption_df = pd.read_excel(file)

    if consumption_df.shape[0] / 24 != correct_shape[0]:
        return 'LenghtError'

    consumption_df.columns = ['time', 'total']
    consumption_df['time'] = pd.to_datetime(consumption_df['time'])

    if consumption_df['time'].dt.year.mean() != int(year) or consumption_df['time'].dt.month.mean() != int(month):
        return 'periodError'
    

    # Потребление за месяц
    consumption = consumption_df['total'].sum()
    matrix_consumption = transform_from_df_to_matrix(consumption_df)

    # Средняя пиковая мощность за месяц
    peak_power = consumption_df.merge(peak_power_df)['total'].mean()

    # Средняя транспортная мощность за месяц
    transport_power_df = consumption_df.merge(transport_power_df)
    transport_power = transport_power_df.groupby(pd.to_datetime(transport_power_df['time'].dt.date))[['total']].max().mean().values[0]

    # Сумма платежа за потребление энергии для 1, 3, 4
    payment_consumption_1 = consumption * consumption_rate_pc1
    payment_consumption_3 = (matrix_consumption.values * pc3_rate_matrix.values).sum()
    payment_consumption_4 = (matrix_consumption.values * pc4_rate_matrix.values).sum()

    # Итоговая таблица
    result = pd.DataFrame(columns=['Ценовая категория 1', 'Ценовая категория 3', 'Ценовая категория 4'])
    result.loc['Потребление'] = [consumption] * 3
    result.loc['Пиковая мощность'] = [0, peak_power, peak_power]
    result.loc['Транспортная мощность'] = [0, 0, transport_power]
    result.loc['Ставка пиковой мощности'] = [peak_power_rate] * 3
    result.loc['Ставка транспортной мощности'] = [transport_power_rate] * 3
    result.loc['Платеж ээ'] = [payment_consumption_1, payment_consumption_3, payment_consumption_4]
    result.loc['Платеж пиковой мощности'] = result.loc['Ставка пиковой мощности'] * result.loc['Пиковая мощность']
    result.loc['Платеж транспортной мощности'] = result.loc['Ставка транспортной мощности'] * result.loc['Транспортная мощность']
    result.loc['Итого платеж'] = result.loc[['Платеж ээ', 'Платеж пиковой мощности', 'Платеж транспортной мощности']].sum()
    result.loc['Взвешенная ставка за 1 кВтч'] = result.loc['Итого платеж'] / result.loc['Потребление']

    # Таблица с ссылками на источники данных
    
    info_df = pd.DataFrame(index=['Тарифы МЭС', 
                                  'Пиковые часы нагрузки', 
                                  'Плановые часы пиковой нагрузки (транспортная мощность)',
                                  'Уровень максимальной мощности',
                                  'Уровень напряжения',
                                  'Регион'
                                ])

    info_df['Ссылки'] = ['https://www.mosenergosbyt.ru/legals/tariffs-n-prices/', 
                            'https://www.atsenergo.ru/results/market/calcfacthour',
                            f'https://www.so-ups.ru/fileadmin/files/company/markets/{year}/pik_chas{year}.pdf',
                            maximum_power_level,
                            voltage_level,
                            region]


    # Запись эксель файла в оперативную память
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        result.to_excel(writer, sheet_name='Результат')
        matrix_consumption.to_excel(writer, sheet_name='Матрица потребления')
        pc3_rate_matrix.to_excel(writer, sheet_name='Ценовая категория 3')
        pc4_rate_matrix.to_excel(writer, sheet_name='Ценовая категория 4')
        info_df.to_excel(writer, sheet_name='Ссылки')
    
        # Доступ к рабочей книге и листу openpyxl
        worksheets = [writer.sheets['Результат'], writer.sheets['Ссылки']]
        
        for worksheet in worksheets:
            # Настраиваем ширину столбцов
            for column in worksheet.columns:
                max_length = 0
                column_name = column[0].column_letter  # Получаем имя столбца
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column_name].width = adjusted_width

                # Настраиваем выравнивание слева для первого столбца
                if column_name == 'A':
                    for cell in column:
                        cell.alignment = Alignment(horizontal='left')
    
        writer.close()

    output_file = io.BytesIO()
    writer.book.save(output_file)
    output_file.seek(0)

    return output_file.getvalue()