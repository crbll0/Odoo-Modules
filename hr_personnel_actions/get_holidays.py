from collections import defaultdict
import datetime
from lxml import html
import requests

def get_data():
    '''
    Hace una peticion a la web officeholidays y...
    Obtiene los dias feriados de todo el anio

    '''

    req = requests.get('http://www.officeholidays.com/countries/dominican_republic/index.php')

    tree = html.fromstring(req.content)

    days = tree.xpath('//span[@class="ad_head_728"]/text()')

    holidays = ['January 01', 'January 04', 'January 21', 'January 25', 'February 27', 'March 25', 'March 27', 'May 02',
            'May 26', 'May 29', 'July 31', 'August 16', 'September 24', 'November 06', 'December 25']



    # Current Month.
    c_month = datetime.date.today().month  #Retorna 1 para enero.

    # Number of Month
    n_month = {
        1:'January', 2:'February',3:'March', 4:'April',
        5:'May', 6:'June',7:'July', 8:'August',
        9:'September', 10:'October',11:'November', 12:'December',
    }

    arrHol = []
    for h in days:
        arrHol.append(h.split(' '))

    HOLIDAYS = defaultdict(list)
    for mes, dia in arrHol:
        HOLIDAYS[mes].append(dia)

    HD = HOLIDAYS[n_month[c_month]]

    return get_dates(HD)

def get_dates(dates=[]):

    m = datetime.date.today().month
    y = datetime.date.today().year
    listFecha = []

    for date in dates:
        fecha = datetime.date(y,m,int(date))
        listFecha.append(fecha)

    return listFecha


print get_data()