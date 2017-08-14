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

storage_path = '/scratch/sy1743/wildlife/ecrater/'

def itemsfromAmazonSERP(url):
    try:
        logging.info(url)
        opener = ur.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        response = opener.open(url)
        html_contents = response.read()
        parsed = bs(html_contents, 'html.parser')
        h3s = parsed.findAll("li", {"class":"product-item"})
        results = []
        for link in h3s:
            results.append("http://www.ecrater.com"+link.find('a').get('href'))
        return results
    except:
        wr = open('error_serp.log','a')
        wr.write(url+'\n')
        wr.close()
        print 'SERP ERROR'
        return []

def getTitle(parsed):
    try:
        title = parsed.findAll('div', {'id': 'product-title'})
        return title[0].find('h1').text
    except:
        return []

def getPrice(parsed):
    try:
        price = parsed.findAll('div', {'id': 'product-title-actions'})
        return price[0].find('span').text.strip().replace('\t','').replace('\r','').replace('\n','')
    except:
        return []

def getDescription(parsed):
    try:
        descs = parsed.findAll('div',{'id':'description'})
        return descs[0].text.strip().replace('\t','').replace('\r','').replace('\n','')
    except:
        return []

def getImages(parsed):
    imgDict = []
    try:
        m = parsed.findAll('div', {'id': 'wBiggerImage'})
        for i in m:
            imgDict.append(i.find('img').get('src'))
        return imgDict
    except:
        return []

def getSeller(parsed):
    try:
        seller = parsed.findAll('div',{'id':'seller-contact'})
        return seller[0].find('a').get('href')
    except:
        return []

def getShippingInfo(parsed):
    info = []
    try:
        ship = parsed.findAll('div',{'id':'product-details'})[0].findAll('p')
        for i in ship:
            info.append(i.text.strip().replace('\t','').replace('\r','').replace('\n',''))
        return info
    except:
        return []

def getID(url):
    try:
        return urlparse.urlparse(url).path.split('/')[2]
    except:
        return 'ecrater_{}_{}'.format(url)

def saveAmazonInfo(info):
    cp.dump(info,open(storage_path + 'dicts/' + str(info['id']) + '.dict', 'w'))

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
        logging.info('ERRORR: {}'.format(url))
        return

def main():
    check_point = int(time.time())
    logging.basicConfig(filename=storage_path + "{}.log".format(check_point), level = logging.DEBUG)

    # import search keyword
    kws_list = pickle.load(open("/scratch/sy1743/wildlife/total_kws_list.p", "rb"))
    url_patt = "http://www.ecrater.com/filter.php?a=1&keywords={}&sort=price_desc&perpage=80"
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
        if i % 100:
            time.sleep(10)

if __name__ == '__main__':
    main()
