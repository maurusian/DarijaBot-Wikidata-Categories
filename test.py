import pywikibot
from urllib.request import urlopen, quote, Request
from urllib.error import URLError
import json, sys, os
#import SPARQLWrapper
import requests

MAIN_QUERY_FILENAME = "./data/query_items.sparql"

RES_FILENAME = {'year':'query_result_years.json','decade':'query_result_decade.json'}

ITEM_TYPES = {'year':'Q577','decade':'Q39911'}

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
        

def rebuild_dict(raw_list):
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
            year = int(year)
            new_dict[year] = elem['category'].split('/')[-1]
        except ValueError:
            print(str(year)+' is not a valid number')
            
        

    return new_dict

print("Prepare raw dict")
#raw_year_dict = dict(get_data(ITEM_TYPES['year']))
raw_year_list = get_data2('year')
print("Raw dict ready")
#print(raw_year_list[0])
print("Prepare year dict")
year_dict = rebuild_dict(raw_year_list)
print(year_dict)
print("Year dict ready")

print("iterate over years")
counter = 0
for key in year_dict.keys():
    en_title = "Category:AD"+str(key)
    ary_title = "تصنيف:"+str(key)
    print(key)
    #print(dict(get_data(ITEM_TYPES['year']))['results']['bindings'][1])
    site = pywikibot.Site()
    repo = site.data_repository()
    #site_en = pywikibot.Site('en','wikipedia')
    #page = pywikibot.Page(site_en, en_title)
    #print(page.getID())
    #item = pywikibot.ItemPage(repo, item_id)
    cat_item = pywikibot.ItemPage(repo,year_dict[key])
    cat_item.get()
    print(list(cat_item.sitelinks.keys()))
    site_ary = pywikibot.Site('ary','wikipedia')
    page = pywikibot.Page(site_ary, ary_title)
    if page.text != '':
        print("Page "+ary_title+" found")
        if 'arywiki' not in cat_item.sitelinks.keys():
            cat_item.setSitelink(page, summary=u'Setting sitelink by adding ary category')
            counter+=1
    if counter > 47:
        break
        
    
