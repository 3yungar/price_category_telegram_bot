import io
import requests
import pandas as pd
import urllib3
import datetime as dt

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

plan_dict = {
    '01': list(range(7, 21)),
    '02': list(range(7, 13)) + list(range(16, 21)),
    '03': list(range(7, 21)),
    '04': list(range(7, 15)) + list(range(17, 21)),
    '05': list(range(7, 15)) + list(range(19, 21)),
    '06': list(range(7, 16)) + list(range(19, 21)),
    '07': list(range(7, 17)) + list(range(19, 21)),
    '08': list(range(7, 21)),
    '09': list(range(7, 15)) + list(range(17, 21)),
    '10': list(range(7, 21)),
    '11': list(range(7, 11)) + list(range(15, 21)),
    '12': list(range(7, 12)) + list(range(14, 21))
}


def parse_hours(period):
    month = period.split('-')[1]
    '''
    Возвращает датафреймы с пиковыми и плановыми часами с сайта https://www.atsenergo.ru
    period: выгружаемый период
    '''
    name_period = period.replace('-', '')
    url = f'https://www.atsenergo.ru/dload/calcfacthour_regions/{name_period}_MOSENERG_46_calcfacthour.xls'
    response = requests.get(url, verify=False)
    with io.BytesIO(response.content) as fh:
        peak_df = pd.io.excel.read_excel(fh, skiprows=6)
        peak_df.columns = ['time', 'peak_hour']
        peak_df = peak_df.drop(index=0)
        peak_df['time'] = pd.to_datetime(peak_df['time'], dayfirst=True)
        fh.close()
    
    # towrite = io.BytesIO()
    # # Записываем датафрейм в буффер
    # df.to_excel(towrite, index=False)
    # towrite.seek(0)
    # return towrite.getvalue()

    peak_df['transport_hour'] = [plan_dict[month] for _ in range(len(peak_df))]

    transport_df = peak_df.explode('transport_hour')
    transport_df['transport_hour'] = transport_df['transport_hour'].apply(lambda x: dt.timedelta(hours=int(x)))
    transport_df['time'] = transport_df['time'] + transport_df['transport_hour']
    transport_df = transport_df.drop(columns=['peak_hour', 'transport_hour'])
    
    peak_df = peak_df.drop(columns='transport_hour')
    peak_df['peak_hour'] = peak_df['peak_hour'].apply(lambda x: dt.timedelta(hours=x))
    peak_df['time'] = peak_df['time'] + peak_df['peak_hour']
    peak_df = peak_df.drop(columns=['peak_hour'])

    return peak_df, transport_df
