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

# ebid

storage_path = '/scratch/sy1743/wildlife/search_by_query/'

def itemsfromAmazonSERP(url):
    try:
        logging.info(url)
        opener = ur.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        response = opener.open(url)
        html_contents = response.read()
        parsed = bs(html_contents, 'html.parser')
        h3s = parsed.findAll("div", {"class":"images subtle-gallery-item"})
        results = []
        for link in h3s:
            results.append(link.find('a').get('href'))
        return results
    except:
        wr = open('error_serp.log','a')
        wr.write(url+'\n')
        wr.close()
        print 'SERP ERROR'
        return []

def getTitle(parsed):
    try:
        title = parsed.findAll('h1', {'class': 'item-title'})
        return title[0].text
    except:
        return []

def getPrice(parsed):
    try:
        price = parsed.findAll('span', {'class': 'converted-price'})
        return price[0].text.strip().replace('\t','').replace('\r','').replace('\n','')
    except:
        return []

def getDescription(parsed):
    try:
        descs = parsed.findAll('div', {'id': 'item-description'})
        return descs[0].text.strip().replace('\t','').replace('\r','').replace('\n','')
    except:
        return []

def getImages(parsed):
    imgDict = []
    try:
        m = parsed.findAll('img', {'class':'thumbnail'})
        for i in m:
            imgDict.append(i.get('src'))
        return imgDict
    except:
        return []

def getSeller(parsed):
    return []

def getShippingInfo(parsed):
    try:
        ship = parsed.findAll('div', {'id': 'item-information'})
        return ship[0].text.strip().replace('\t','').replace('\r','').replace('\n','')
    except:
        return []

def getID(url):
    return urlparse.urlparse(url).path.split('-')[-1] + '_' + str(int(time.time()))

def saveAmazonInfo(info):
    cp.dump(info, open(storage_path + 'dicts/' + str(info['id']) + '.dict', 'w'))

def saveHtml(id,page):
    cp.dump(page, open(storage_path + 'htmls/' + str(id) + '.html', 'w'))

def getInfofromAmazon(url,src):
    ## make provisions for
    ## 1. reading from saved html and not read url
    ## 2. not save html if already saved
    amazondict = {}
    try:
        if src == 'url':
            opener = ur.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            response = opener.open(url)
            html_contents = response.read()
        elif src == 'file':
            page = open(storage_path + 'htmls/' + url).read()

        parsed_page = bs(html_contents, 'html.parser')
        amazondict['id'] = getID(url)
        ## asserting the ids match when read from a file
        if src == 'file':
            if url[:-5] != str(amazondict['id']):
                wr = open('mismatch.log', 'w')
                wr.write(url + '\n')
                wr.close()
        if src == 'url':
            saveHtml(amazondict['id'], html_contents)

        amazondict['images'] = getImages(parsed_page)
        amazondict['price'] = getPrice(parsed_page)
        amazondict['title'] = getTitle(parsed_page)
        amazondict['seller'] = getSeller(parsed_page)
        amazondict['url'] = url
        amazondict['shipping_info'] = getShippingInfo(parsed_page)
        amazondict['description_links'] = getDescription(parsed_page)
        saveAmazonInfo(amazondict)
        logging.info('Success:{}, url:{}'.format(amazondict['id'], url))

    # return amazondict
    except:
        wr = open(storage_path + 'error.log', 'a')
        wr.write(url + '\n')
        wr.close()
        logging.info('ERROR: {}'.format(url))
        return

def main():
    check_point = int(time.time())
    logging.basicConfig(filename=storage_path + "{}.log".format(check_point), level = logging.DEBUG)

    # import search keyword
    kws_list = pickle.load(open("/scratch/sy1743/wildlife/total_kws_list.p", "rb"))
    url_patt = "http://www.ioffer.com/search/items/{}?order=price_desc"
    url_list = map(lambda x: url_patt.format(x), kws_list)
    logging.info('generating all item list...')
    item_list = []
    for url in url_list:
        item_list.extend(np.unique(itemsfromAmazonSERP(url)))
    total = len(item_list)
    logging.info('collecting item information...')
    for i, item in enumerate(item_list):
        logging.info('{}/{} processed'.format(i, total))
        getInfofromAmazon(item, src='url')
        if i % 500:
            time.sleep(3)

if __name__ == '__main__':
    main()
