import pywikibot
from pywikibot.exceptions import OtherPageSaveError, APIError, InvalidTitleError
from urllib.request import urlopen, quote, Request
from urllib.error import URLError
import json, sys, os
#import SPARQLWrapper
import requests

MAIN_QUERY_FILENAME = "./data/query_items.sparql"

RES_FILENAME = {'year':'query_result_years.json'
               ,'decade':'query_result_decade.json'
               ,'birth year':'query_result_birth_years.json'
               ,'death year':'query_result_death_years.json'
               ,'birth decade':'query_result_birth_decades.json'
               ,'death decade':'query_result_death_decades.json'}

ITEM_TYPES = {'year':'Q577','decade':'Q39911','birth year':'','death year':'','birth decade':'','death decade':''}

CAT_PART_DICT = {'year':'تصنيف:','decade':'تصنيف:عوام ','birth year':'تصنيف:زيادة ','death year':'تصنيف:وفيات ','birth decade':'تصنيف:زيادة ف عوام ','death decade':'تصنيف:وفيات ف عوام '}

LOG_PAGE_TITLE = 'User:DarijaBot/log'

def log_error(LOG_PAGE_TITLE,log_message,site):
    log_page = pywikibot.Page(site, LOG_PAGE_TITLE)
    if log_page.text != '':
        log_page.text += '\n* '+log_message
    else:
        log_page.text = '* '+log_message

    log_page.save('Added log entry')

def get_data(item_type_id):
    """
    Sends query to retrieve year/decade categories
    with corresponding year/decade in a raw json structure
    """
    with open(MAIN_QUERY_FILENAME,'r') as f:
        query = f.read().replace('{item_type_id}',item_type_id)

    url = "https://darijabot@query.wikidata.org/sparql?query=%s&format=json" % quote(query)
    #headers are necessary, without user-agent the Wikidata server refuses to connect, and without the charset ensues a Unicode error
    headers = {
        'User-Agent': 'DarijaBot/0.1 (Edition Windows 10 Home, Version 20H2, OS build 19042.1165, Windows Feature Experience Pack 120.2212.3530.0) Python3.9.0',
        'Content-Type': 'text/text; charset=utf-8'
    }
    response = requests.get(url, headers=headers)
    res      = response.json()
    if response is not None:
        #res = json.loads(response)
        res      = response.json()
        return res
    else:
        return {}

def get_data2(item_type_id):
    
    with open('./data/'+RES_FILENAME[item_type_id],'r') as f:
        return eval(f.read())
        

def rebuild_year_dict(raw_list):
    """
    Converts raw dictionary (json) obtained by a wikidata query
    to a more useful dictionary with years as keys, and category
    item ID as values.
    """
    new_dict = {}
    for elem in raw_list:
        year = elem['itemLabel']
        if 'AD' in year:
            year = year[3:]

        try:
            if "BC" in year:
                year = year[:-3]
                year = 0 - int(year)
                print("BC year: "+str(year))
            else:
                year = int(year)
            new_dict[year] = elem['category'].split('/')[-1]
        except ValueError:
            print(str(year)+' is not a valid number')
            
        

    return new_dict


def rebuild_decade_dict(raw_list):
    """
    Converts raw dictionary (json) obtained by a wikidata query
    to a more useful dictionary with decades as keys, and category
    item ID as values.
    """
    new_dict = {}
    for elem in raw_list:
        decade = elem['itemLabel'].replace('s','')
        if 'AD' in decade:
            decade = decade[3:]

        try:
            if "BC" in decade:
                decade = decade[:-3]
                decade = 0 - int(decade)
            else:
                decade = int(decade)
            
            new_dict[decade] = elem['category'].split('/')[-1]
        except ValueError:
            print(str(decade)+' is not a valid number')
            
    return new_dict

def rebuild_birth_death_periods_dict(raw_list):
    """
    Converts raw dictionary (json) obtained by a wikidata query
    to a more useful dictionary with year as keys, and category
    item ID for the birth/death year/decade as values.
    """
    new_dict = {}
    for elem in raw_list:
        period = elem['itemLabel'][9:-7].replace('s','').replace('AD','').strip() #remove 's', 'AD' and starting/trailing spaces from string

        try:
            if "BCE" in period:
                period = period[:-4]
                period = 0 - int(period)
            elif "BC" in period:
                period = period[:-3]
                period = 0 - int(period)
            else:
                period = int(period)
            
            new_dict[period] = elem['item'].split('/')[-1]
        except ValueError:
            print(str(period)+' is not a valid number')
            
    return new_dict

def rebuild_period_type_dict(raw_period_type_list,period_type):
    if period_type == 'year':
        return rebuild_year_dict(raw_period_type_list)
    elif period_type == 'decade':
        return rebuild_decade_dict(raw_period_type_list)
    else:
        return rebuild_birth_death_periods_dict(raw_period_type_list)

def run_for_period_type(period_type):
    print("Prepare raw dict")
    #raw_year_dict = dict(get_data(ITEM_TYPES['year']))
    raw_period_type_list = get_data2(period_type)
    print("Raw dict ready")
    #print(raw_year_list[0])
    print("Prepare period_type dict")
    period_type_dict = rebuild_period_type_dict(raw_period_type_list,period_type)
    print(period_type_dict)
    print("Year dict ready")

    print("iterate over years")
    counter = 0
    for key in period_type_dict.keys():
        
        
        if key < 0:
            ary_title = CAT_PART_DICT[period_type]+str(0-key)+" قبل لميلاد"
        else:
            ary_title = CAT_PART_DICT[period_type]+str(key)
        
        site = pywikibot.Site()
        repo = site.data_repository()
        
        cat_item = pywikibot.ItemPage(repo,period_type_dict[key])
        cat_item.get()
        
        site_ary = pywikibot.Site('ary','wikipedia')
        page = pywikibot.Page(site_ary, ary_title)
        if page.text != '':
            print("Page "+ary_title+" found")
            if 'arywiki' not in cat_item.sitelinks.keys():
                try:
                    cat_item.setSitelink(page, summary=u'Setting sitelink by adding ary category')
                    counter+=1
                except OtherPageSaveError:
                    log_error(LOG_PAGE_TITLE,str(sys.exc_info()),site)
                    print(sys.exc_info())
                except APIError:
                    log_error(LOG_PAGE_TITLE,str(sys.exc_info()),site)
                    print(sys.exc_info())
                except InvalidTitleError:
                    log_error(LOG_PAGE_TITLE,str(sys.exc_info()),site)
                    print(sys.exc_info())
                    
            
    print(str(counter)+" objects linked")


#run for years
run_for_period_type('year')

#run for decades
run_for_period_type('decade')

#run for birth years
run_for_period_type('birth year')

#run for death years
run_for_period_type('death year')

#run for death years
run_for_period_type('birth decade')

#run for death years
run_for_period_type('death decade')
