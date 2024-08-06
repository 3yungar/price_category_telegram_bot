from io import BytesIO
import requests
import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup



def get_tariff_url(maximum_power_level, period):
    '''
    Возвращает url-адрес для скачивания тарифа с сайта https://mosenergosbyt.ru
    maximum_power_level: категория максимальной мощности;
    period: период, по которому выгружается тариф;
    '''
    def get_upload_reference(child):
        # поиск тегов ссылки и описания по периоду
        links_tags = child.findChildren('a', {'class': 'item-link'})
        titles_tags = child.findChildren('div', {'class': 'item-title'})

        months = {
            'январе': '01',
            'феврале': '02',
            'марте': '03',
            'апреле': '04',
            'мае': '05',
            'июне': '06',
            'июле': '07',
            'августе': '08',
            'сентябре': '09',
            'октябре': '10',
            'ноябре': '11',
            'декабре': '12'
        }

        for title, link in zip(titles_tags, links_tags):
            title = title.get_text().strip()
            name_month, year = title.split()[-2:]
            if f'{year}-{months[name_month]}' == period:
                upload_reference = 'https://mosenergosbyt.ru' + link.get('href')
                break
        else:
            upload_reference = None

        return upload_reference



    year, _ = period.split('-')
    mosenergosbyt_url = 'https://www.mosenergosbyt.ru/legals/tariffs-n-prices/'

    # Переход на страницу с тарифами согласно максимальной мощности
    html = urlopen(mosenergosbyt_url)
    soup = BeautifulSoup(html, 'html.parser')
    children = soup.findChildren('a', {'class': 'card'})

    for child in children:
        description_maximum_power_level = child.getText()
        if description_maximum_power_level == maximum_power_level:
            current_url = 'https://www.mosenergosbyt.ru' + child.get('href')
            html = urlopen(current_url)
            child = BeautifulSoup(html, 'html.parser')
            break # вернет нужный псевдокласс согласно максимальной мощности


    upload_reference = get_upload_reference(child)

    if upload_reference is None:
        # проверка на наличие указанного периода в архиве
        info_archives_url = 'https://www.mosenergosbyt.ru/legals/tariffs-n-prices/archive/'
        archives_html = urlopen(info_archives_url)
        archive_soup = BeautifulSoup(archives_html, 'html.parser')
        # псевдокласс, состоящий из ссылок на года
        archive_children = archive_soup.findChildren('a', {'class': 'item-link d-table-cell'})

        inArchive = False # флаг на отсутствие в архиве
        for archive_child in archive_children:
            if archive_child.getText() == year:
                # ссылка на архив с тарифами в соответствии с годом введенного периода
                archive_url = 'https://www.mosenergosbyt.ru/' + archive_child.get('href')
                inArchive = True # флаг на присутствие в архиве

        # получение псевдокласса с ссылками на скачивание тарифов МЭС
        if inArchive: # тарифы в архиве
            html = urlopen(archive_url)
            soup = BeautifulSoup(html, 'html.parser')
            children = soup.findChildren('div', {'class': 'item'})
            # поиск в архиве псевдокласса согласно ограничению на максимальную мощность
            for child in children:
                description_maximum_power_level = child.findChild().getText().strip()
                if description_maximum_power_level == maximum_power_level:
                    break # вернет нужный псевдокласс
            
            upload_reference = get_upload_reference(child) 
        else:
            upload_reference = None
    
    return upload_reference


def get_tariff_excel_file(maximum_power_level, period):
    '''
    Возвращает эксель файл с тарифами с сайта https://mosenergosbyt.ru
    maximum_power_level: категория максимальной мощности;
    period: период, по которому выгружается тариф
    '''

    url = get_tariff_url(maximum_power_level, period)
    if url is None:
        return None
    
    response = requests.get(url)
    # байтовое представление файла
    # file = io.BytesIO(response.content).read()
    # return file
    tariff_xl = pd.ExcelFile(BytesIO(response.content))
    return tariff_xl
