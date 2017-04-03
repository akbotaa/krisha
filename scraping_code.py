import requests as rqst
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import openpyxl
from datetime import date, timedelta
import re, os
import math


#============================================================

# manually change room number and oblast, could loop through them
# but code runs too long (visiting so many pages is expensive), so better to run piece by piece

o_i = 3 #oblast index from 0 to 15

r_i = 1 #room index from 0 to 4 (this should be changed for each value of o_i)


#============================================================
##------------------- define variables --------------------##

room_num_list = ['1', '2', '3', '4', '5.999']

oblast_list = ['astana', 'almaty', 'akmolinskaja-oblast', 'aktjubinskaja-oblast', 'almatinskaja-oblast', \
                'atyrauskaja-oblast', 'vostochno-kazahstanskaja-oblast', 'zhambylskaja-oblast', \
                'zapadno-kazahstanskaja-oblast', 'karagandinskaja-oblast', 'kostanajskaja-oblast', \
                'kyzylordinskaja-oblast', 'mangistauskaja-oblast', 'pavlodarskaja-oblast', \
                'severo-kazahstanskaja-oblast', 'juzhno-kazahstanskaja-oblast']
                
oblast_list_rus = ['Астана', 'Алматы', 'Акмолинская обл.', 'Актюбинская обл.', 'Алматинская обл.', \
                'Атырауская обл.', 'Восточно-Казахстанская обл.', 'Жамбылская обл.', \
                'Западно-Казахстанская обл.', 'Карагандинская обл.', 'Костанайская обл.', \
                'Кызылординская обл.', 'Мангистауская обл.', 'Павлодарская обл.', \
                'Северо-Казахстанская обл.', 'Южно-Казахстанская обл.']
                    
column_list = ['Цена', 'Комнаты', 'Область/Город', 'Район/Город', 'Адрес', 'Дом', 'Жилой комплекс', \
                'Этаж', 'Площадь', 'Состояние', 'Санузел', 'Балкон', 'Балкон остеклен', 'Потолки', \
                'В залоге', 'В прив. общежитии', 'Безопасность', 'Дополнительно', 'Комментарии']
                
kz = 'Казахстан'
today = date.today()
folder = str(today)
data_path = '/Users/akbota/Documents/summer, 2016/Prof.Becker RA/krisha data/' #<- folder where data will be stored


##------------------- functions ---------------------------##

def krisha_spider(rooms, oblast, oblast_rus, page = 1, max_pages = 2):
    
    data = pd.DataFrame(columns = column_list)

    while page <= max_pages:
        counter = 1
        if page==1:
            print('Scraping page ' + str(page))
        else:
            print('Scraping page ' + str(page) + ' of ' + str(max_pages))
        
        ##-------------------------crawl the main page--------------------------
        
        url = 'http://krisha.kz/prodazha/kvartiry/' + oblast + '/?das[live.rooms]='+ rooms + '&page=' + str(page)
        source_code = rqst.get(url)
        plain_text = source_code.text
        soup = BeautifulSoup(plain_text, "html.parser")
        
            
        ##---find all anouncement links -> loop through them and scrape data----
        
        for div in soup.findAll('div', {'class': 'a-title'}):
        
            item_url = div.find('a', {'class': 'link'})['href']
         
            item_src_code = rqst.get('https://krisha.kz' + item_url)
            item_soup = BeautifulSoup(item_src_code.text, "html.parser")
    
    
            #---item id
            item_id = item_url[-8:]
    
            #---item price
            price = item_soup.find('span', {'class': 'price'})
            price.span.replace_with('')
    
            data.loc[item_id, 'Цена'] = price.text
    
            #--is mortgaged
    
            is_mortgaged = item_soup.find('div', {'class': 'a-is-mortgaged'})
            if is_mortgaged is None:
                data.loc[item_id, 'В залоге'] = 'нет'
            else:
                data.loc[item_id, 'В залоге'] = 'да'
    
            #---date data was collected
    
            data.loc[item_id, 'Дата'] = today
    
            #---other comments
    
            additional = item_soup.find('div', {'class': 'a-options-text'})
            comment = item_soup.find('div', {'class': 'a-text'})
    
            if additional is not None:
                data.loc[item_id, 'Дополнительно'] = additional.string
            if comment is not None:
                data.loc[item_id, 'Комментарии'] = comment.string
    
            #---other parameters
    
            params = item_soup.find('dl', {'class': 'a-parameters'})

            #----replace strange tags to make data readable----#
            for s in params.findAll('sup'):
                params.sup.replace_with('кв')

            params=str(params)
            params = BeautifulSoup(params, "html.parser")
            #--------------------------------------------------#
    
            keys = params.findAll('dt')
            values = params.findAll('dd')
    
    
            data.loc[item_id, 'Область/Город'] = oblast_rus
    
    
            for k, v in list(zip(keys, values)):
                data.loc[item_id, k.string] = v.string
    
            rg = item_soup.find('div', {'class': 'a-where-region'})
            if rg is not None:
                region = rg.string.split(', ')[-1]
            else:
                data = data[data.index != item_id]
                print('Sth is wrong! Proceed to the next!')
                continue
        
            adresdiv = item_soup.find('div', {'class': 'a-header-wrapper'})
            adresdiv = BeautifulSoup(str(adresdiv), "html.parser")
            adreslist = adresdiv.find('h1').string.split(', ')[1:]
            adres = ', '.join(adreslist)
            
            if rooms=='5.999':
                data.loc[item_id, 'Комнаты'] = adresdiv.find('h1').string.split('-комн')[0]
            else:
                data.loc[item_id, 'Комнаты'] = rooms
        
            if 'р-н' in adres:
                data.loc[item_id, 'Район/Город'] = adres
            else:
                if region!=oblast_rus and region!=kz:
                    data.loc[item_id, 'Район/Город'] = region
                if adres!=oblast_rus:
                    data.loc[item_id, 'Адрес'] = adres
                    
    
            print(counter)
            counter+=1
        
        
        ##----scrape max page number here
        if page==1:
           
            total_ads_str = soup.find('div', {'class': 'a-search-subtitle search-results-nb'}).find('span').string.split()
           
            total_ads = int(''.join(total_ads_str))
            max_pages = math.ceil(total_ads/20)
            print('max pages:' + str(max_pages))
            
        page += 1
    
    return(data)   




def save_to_xl(df, obl, path, r):
    
    print('saving data...')    
    
    if not os.path.isdir(path + folder):
        os.mkdir(path + folder)
        
    full_path = path + folder + '/' + obl
    
    if not os.path.isdir(full_path):
        os.mkdir(full_path)
    
    fname = obl + ' - ' + r + ' room(s)' + '.xlsx'
    
    df.to_excel(full_path + '/' + fname)



##-------------------- run everything ---------------------##
 
rooms = room_num_list[r_i]

oblast = oblast_list[o_i]
oblast_rus = oblast_list_rus[o_i]

if rooms=='5.999':
    rooms_act='5 or more'
else:
    rooms_act = rooms

print(oblast_rus)
print(str(rooms_act) + ' room(s)')

krisha_df = krisha_spider(rooms = rooms, oblast = oblast, oblast_rus = oblast_rus)       
        
save_to_xl(df=krisha_df, obl=oblast, path=data_path, r=rooms_act)

        
        
            