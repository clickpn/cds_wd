import pickle
import re
import os
# import db_script as dbs
from pymongo import MongoClient
import pandas as pd

def modify_format(data, term):
    res = {}
    try:
        site_name = re.search('www.(.*).com',data['url']).group(1)
    except AttributeError:
        site_name = 'alaskanorthtaxidermy'

    res["_id"] = {"id": data['id'], "site": site_name}
    res["artifacts"] = ""
    res['categories'] = []
    res['country'] = 'United States'
    res['desc_text'] = data['description_links']
    res['date_searched'] = '2017-06-06'
    res['image_urls'] = data['images']
    res['label'] = {'old_rel_score': -1, 'rel_score': -1}
    res['misc_info'] = {"main_image":"", "overview-materials":[]}
    if len(data['price']) != 0:
        if 'This item' in data['price']:
            tmp_price = re.findall(r'\d+', data['price'])[:-2]
            if len(tmp_price) > 0:
                price = float(''.join(tmp_price))/100
            else:
                price = -1
        else:
            tmp_price = re.findall(r'\d+', data['price'])[:3]
            price = float(''.join(tmp_price))/100
    else:
        price = -1
    res['price_info'] = {"converted": price, "currency": "USD", "price": price}
    if len(data['seller']) > 0:
        res['seller_info'] = data['seller']
    else:
        res['seller_info'] = {}
    res['shipping_info'] = data['shipping_info']
    res['species'] = ''
    res['title'] = data['title']
    res['url'] = data['url']
    res['search_term'] = term
    return res

# pa = '/Users/sidaye/Desktop/search_by_query_0609/data/abalone/dicts'
# fns = [os.path.join(pa, x) for x in os.listdir(pa) if 'dict' in x]
# fns = [pickle.load(open(x)) for x in fns]
# fns = [modify_format(x, 'abalone') for x in fns]
# mod_pa = '/Users/sidaye/Desktop/wildlife_mongoDB_Sida/wildlife_0601/ebay/mod_dicts'
# for x in fns:
#     pickle.dump(x, open(os.path.join(mod_pa, '{}.dict'.format(x['_id']['id'])), "wb"))

# import to mongoDB
