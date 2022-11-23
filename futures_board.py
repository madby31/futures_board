#!/usr/bin/env python
# coding: utf-8
# ver 1.1
from tkinter import Tk, ttk, BooleanVar, StringVar
import webbrowser
import math
import datetime
import urllib.request
import requests as re
import pandas as pd
import json
from html2image import Html2Image
from ticket_quartal import ticket_quartal, unit_month

now = datetime.datetime.now()
now = datetime.datetime.date(now)
today_month = int(now.month)

if today_month in [3,6,9,12]:
    quarter = today_month
else:
    quarter = (math.trunc(int(today_month)/3)+1)*3
today_year = str(now.strftime("%Y")[3:4])

def get_ticket(tick, quartal, today_month, year):
    if quartal=='Q':
        month = unit_month[quarter]
    elif quartal=='NM':
        if today_month != 12:
            month = unit_month[today_month+1]
        else:
            month = unit_month[1]
    elif quartal=='CM':
        month = unit_month[today_month]
    full_ticket = tick+month+year
    return full_ticket

# Читаем список тикетов
with open('input.txt', 'r') as file_name:
    names = file_name.read().splitlines()

with open('settings.txt', 'r') as file_name:
    settings = file_name.read().splitlines()
token = settings[1]
channel_id = settings[3]
text_telegram = settings[5]
xx = int(settings[8])
yy = 505

def print_sel():
    root.quit()

root = Tk()
root.iconbitmap('favicon.ico')
root.title('Фьючерсы Московской биржи')
chk = {}
col = 0
rows = 0
for ind in names:
    ticket, btype = ind.split()
    if ticket[0:1] == '=':
        chk[ticket] = StringVar(value=btype)
        ttk.Label(root, text=btype).grid(column=1, row=rows+1, sticky='W', padx=20, pady=5)
        col = 0
        rows = rows+2
    else:
        chk[ticket] = BooleanVar()
        chk[ticket].set(btype)
        ttk.Checkbutton(root, text=ticket, var=chk[ticket]).grid(column=col, row=rows, sticky='W', padx=20)
        col += 1
        if col == 3:
            col = 0
            rows += 1

telegram = BooleanVar()
telegram.set(False)
ttk.Checkbutton(root, text='Отправить в Телеграм', var=telegram).grid(column=1, row=rows+1, sticky='W', padx=20, pady=5)
ttk.Button(root, text="OK", command=print_sel).grid(column=1, row=rows+2, sticky='W', padx=20, pady=5)
root.mainloop()

ticket_data = []
datasave = []
for nam in names:
    ticket, btype = nam.split()
    datasave.append(ticket+' '+str(chk[ticket].get()))
    if chk[ticket].get() == True:
        ticket_data.append(ticket)

with open('input.txt', 'w') as file_name:
    file_name.writelines("%s\n" % line for line in datasave)
df = pd.DataFrame()
df['Название'] = ['Цена', 'Шаг цены', 'Стоимость шага цены', 'Сбор', 'Стоимость контракта', 'ГО, руб.', 'Возможная загрузка (Х*депо)', 'Доля шага в стоимости, %', 'Шаг с загрузкой депо, %']
for ticket in ticket_data:
    tick, quartal = ticket_quartal[ticket]
    full_ticket = get_ticket(tick, quartal, today_month, today_year)
    url = 'https://iss.moex.com/iss/engines/futures/markets/forts/boards/RFUD/securities/'+full_ticket+'.jsonp'
    html = json.loads(urllib.request.urlopen(url).read().decode("utf-8"))
    headers = html['securities']['columns']
    data = html['securities']['data'][0]
    depo = round((float(data[18]) / float(data[6]) * float(data[17])), 2)
    loading = round(depo/float(data[14]),2)
    part_step = round((float(data[17])/depo*100),3)
    full_part_step = round((part_step*loading),3)
    df[ticket] =[ data[18], data[6], data[17], data[21], depo, data[14], loading, part_step, full_part_step]

html_string = '''
<html>
  <head>
  <link href="https://allfont.ru/allfont.css?fonts=a_lcdnova" rel="stylesheet" type="text/css" />
  <link rel="shortcut icon" href="favicon.png" type="image/x-icon">
  <title>Фьючерсы Московской биржи</title>
  </head>
  <link rel="stylesheet" type="text/css" href="df_style.css"/>
  <body bgcolor="green">
    {table}
  </body>
</html>.
'''
df.to_csv('table.csv', header=True, sep=";", encoding="cp1251", decimal=",", index=False)
with open('data.html', 'w') as file_name:
    file_name.write(html_string.format(table=df.to_html(index=False, justify='center',classes='mystyle')))
webbrowser.open('data.html')

if telegram.get() == True:
    hti = Html2Image()
    hti.screenshot(
        html_file='data.html', css_file='df_style.css',
        save_as='telscreen.png', size=(xx, yy)
    )
    url = 'https://api.telegram.org/bot'
    pic = open('telscreen.png', 'rb')
    url += token
    method = url + '/sendPhoto'
    r = re.post(method, data={
        'chat_id': channel_id,
        'caption': text_telegram,
        'parse_mode': 'HTML'
    },
        files={
            'photo': pic
        })
    if r.status_code != 200:
        raise Exception('post_text error')
