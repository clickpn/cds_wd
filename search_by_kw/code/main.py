import ioffer
import ecrater
import ebay
import boneroom
import urllib2 as ur
from bs4 import BeautifulSoup as bs
import cPickle as cp
import json
import os
import numpy as np
import cookielib
import urllib
import time
import requests
import logging
import urlparse
import pickle
import argparse

parser = argparse.ArgumentParser(description='query')
parser.add_argument('--kws', type=str,
                    help='query path')
args = parser.parse_args()
keyword_path = args.kws

url_patt_dict = {
    'ecrater': "http://www.ecrater.com/filter.php?a=1&keywords={}&sort=price_desc&perpage=80",
    'ebay': "http://www.ebay.com/sch/i.html?_from=R40&_sacat=0&_oac=1&_nkw={}&_sop=16",
    'ioffer': "http://www.ioffer.com/search/items/{}?order=price_desc",
    'boneroom': "http://www.boneroom.com/apps/search?q={}",
    'alaskanorthtaxidermy': "http://search.store.yahoo.net/yhst-66562580642243/cgi-bin/nsearch?query={}&searchsubmit=Go&vwcatalog=yhst-66562580642243&.autodone=http%3A%2F%2Falaskanorthtaxidermy.com%2F",
    'glacierwear': "http://www.glacierwear.com/catalogsearch/result/index/?ajaxcatalog=true&dir=desc&limit=24&order=price&q={}",
    'skullsunlimited': "http://www.skullsunlimited.com/search_results.php?search_term={}",
    'taxidermy_store': "http://www.thetaxidermystore.com/catalogsearch/result/index/?cat=0&dir=desc&limit=60&order=sku&q={}"
}

def by_web(web_name, keyword):
    new_module = __import__(web_name)
    new_module.storage_path = '../data/{}/'.format(keyword)
    url = url_patt_dict[web_name].format(keyword)
    item_list = new_module.itemsfromAmazonSERP(url)
    total = len(item_list)
    logging.info("="*20)
    logging.info('collecting {} from {} ...'.format(keyword, web_name))
    for i, item in enumerate(item_list):
        logging.info('{}/{} processed'.format(i, total))
        new_module.getInfofromAmazon(item, src='url')
        if i % 500:
            time.sleep(2)

def main():
    kws_list = cp.load(open(keyword_path))
    storage_path = '../logs/'
    for keyword in kws_list:
        check_point = int(time.time())
        logging.basicConfig(filename=storage_path + "{}_{}.log".format(keyword, check_point), level = logging.DEBUG)
        try:
            os.makedirs('../data/{}/dicts'.format(keyword))
            os.makedirs('../data/{}/htmls'.format(keyword))
        except OSError, e:
            if e.errno != 17:
                raise 

        for web in url_patt_dict:
            by_web(web, keyword)

if __name__ == '__main__':
    main()
