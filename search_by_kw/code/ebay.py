import urllib2 as ur
from bs4 import BeautifulSoup as bs
import cPickle as cp
import json
import os
import nltk
import numpy as np
import cookielib
import urllib
import time
import requests
import logging
import urlparse
import pickle

# ebid

storage_path = '/scratch/sy1743/wildlife/ebay/'

def itemsfromAmazonSERP(url):
    try:
        logging.info(url)
        page = ur.urlopen(url).read()
        parsed = bs(page)
        h3s = parsed.findAll('h3')
        results = []
        for h in h3s:
            t = h.findAll('a')
            if len(t) > 0:
                results.append(t[0].get('href'))
        return results
    except:
        wr = open('error_serp.log','a')
        wr.write(url+'\n')
        wr.close()
        print 'SERP ERROR'
        return []

def getTitle(parsed):
    try:
        title = parsed.html.head.title
        return title.text.split('|')[0].strip().lower()
    except:
        return []

def getPrice(parsed):
    try:
        price = parsed.findAll('span', {'itemprop': 'price'})
        return price[0].text.strip().replace('\t','').replace('\r','').replace('\n','')
    except:
        return []

def getDescription(parsed):
    return [k.get('src') for k in parsed.findAll('iframe') if k.get('id') == 'desc_ifr']

# def getImages(parsed):
#     imgDict = []
#     try:
#         m = parsed.findAll('img', {'style': 'max-width:64px;max-height:64px'})
#         for i in m:
#             imgDict.append(i.get('src'))
#         return imgDict
#     except:
#         return []

def getImages(page):
    imgDict = []
    m = page.find('imgArr')
    s = page[m:].find('[')
    e = page[m:].find(']')
    try:
        images = json.loads(page[m + s:m + e + 1])
        for image in images:
            tmp = {}
            tmp['displayImgUrl'] = image['displayImgUrl']
            tmp['maxImageUrl'] = image['maxImageUrl']
            imgDict.append(tmp)
        return imgDict
    except:
        return []

def getSeller(parsed):
    try:
        seller = {}
        members = [k for k in parsed.findAll('a') if k.get('aria-label')!=None and 'Member ID:' in k.get('aria-label')]
        seller['url']=members[0].get('href')
        seller['name'] = members[0].text
        return seller
    except:
        return []

def getShippingInfo(parsed):

    postal_dict = {}
    try:
        postal_dict['item_location'] = [k.text.strip().replace('Item location:','') for k in parsed.findAll('div') if k.get('id')=='itemLocation']

        postal_dict['posts_to'] = [k.text.strip() for k in parsed.findAll('div') if k.get('id')=='vi-acc-shpsToLbl-cnt']
        postal_dict['delivery'] = [k.text.strip() for k in parsed.findAll('div') if k.get('class') != None and 'sh-del-frst' in k.get('class')]
        return postal_dict
    except:
        return []

def getID(url):
    return urlparse.urlparse(url).path.split('/')[-1]

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
            page = ur.urlopen(url).read()
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

        amazondict['images'] = getImages(page)
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
    url_patt = "http://www.ebay.com/sch/i.html?_from=R40&_sacat=0&_oac=1&_nkw={}&_sop=16"
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
        if i % 1000:
            time.sleep(2)

if __name__ == '__main__':
    main()
