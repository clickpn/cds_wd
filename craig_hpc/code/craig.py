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


# storage_path = './{}/'.format(city_name)

def itemsfromAmazonSERP(url, city_name):
    try:
        logging.info(url)
        opener = ur.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        response = opener.open(url)
        html_contents = response.read()
        parsed = bs(html_contents, 'html.parser')
        h3s = parsed.findAll("li", {"class":"result-row"})
        results = []
        for link in h3s:
            tmp = link.find('a').get('href')
            if '//' in tmp:
                results.append(tmp)
            else:
                results.append("https://{}.craigslist.org".format(city_name)+tmp)
        return results
    except:
        wr = open('error_serp.log','a')
        wr.write(url+'\n')
        wr.close()
        logging.info('SERP ERROR')
        return []

def getTitle(parsed):
    try:
        title = parsed.findAll('span', {'id': 'titletextonly'})
        return title[0].text
    except:
        return []

def getPrice(parsed):
    try:
        price = parsed.findAll('span', {'class': 'price'})
        return price[0].text.strip().replace('\t','').replace('\r','').replace('\n','')
    except:
        return []

def getDescription(parsed):
    try:
        descs = parsed.findAll('section', {'id': 'postingbody'})
        return descs[0].text.strip().replace('\t','').replace('\r','').replace('\n','')
    except:
        return []

def getImages(parsed):
    imgDict = []
    try:
        tmp = parsed.findAll('div', {'id':'thumbs'})
        if tmp != []:
            m = tmp[0].findAll('img')
            for i in m:
                imgDict.append(i.get('src'))
            return imgDict
        else:
            imgDict.append(parsed.findAll('div',{'class':'gallery'})[0].find('img').get('src'))
            return imgDict
    except:
        return []

def getSeller(parsed, city_name):
    try:
        seller = parsed.findAll('span',{'class':'replylink'})
        return "https://{}.craigslist.org".format(city_name)+seller[0].find('a').get('href')
    except:
        return []

def getShippingInfo(parsed):
    return []

def getID(url):
    return urlparse.urlparse(url).path.split('/')[-1].split('.')[0] + '_' + str(int(time.time()))

def saveAmazonInfo(info, storage_path):
    cp.dump(info, open(storage_path + 'dicts/' + str(info['id']) + '.dict', 'w'))

def saveHtml(id, page, storage_path):
    cp.dump(page, open(storage_path + 'htmls/' + str(id) + '.html', 'w'))

def getInfofromAmazon(url,src, city_name, storage_path):
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
            saveHtml(amazondict['id'], html_contents, storage_path)

        amazondict['images'] = getImages(parsed_page)
        amazondict['price'] = getPrice(parsed_page)
        amazondict['title'] = getTitle(parsed_page)
        amazondict['seller'] = getSeller(parsed_page, city_name)
        amazondict['url'] = url
        amazondict['shipping_info'] = getShippingInfo(parsed_page)
        amazondict['description_links'] = getDescription(parsed_page)
        saveAmazonInfo(amazondict, storage_path)
        logging.info('Success:{}, url:{}'.format(amazondict['id'], url))

    # return amazondict
    except:
        wr = open(storage_path + 'error.log', 'a')
        wr.write(url + '\n')
        wr.close()
        logging.info('ERROR: {}'.format(url))
        return

def main():
    kws_list = cp.load(open(keyword_path))
    kws_list_par = kws_list[10:]
    city_list = ['bakersfield', 'chico', 'fresno', 'goldcountry', 'hanford', 'humboldt',
     'imperial', 'inlandempire', 'losangeles', 'mendocino', 'merced', 'modesto',
      'monterey', 'orangecounty', 'palmsprings', 'redding', 'reno', 'sacramento', 'sandiego',
       'slo', 'santabarbara', 'santamaria', 'sfbay', 'siskiyou', 'stockton', 'susanville',
       'ventura', 'visalia', 'yubasutter']
    city_list_sub = ['sfbay', 'losangeles', 'sandiego']

    url_patt = "https://{}.craigslist.org/search/sss?sort=pricedsc&query={}"
    for keyword in kws_list_par:
        check_point = int(time.time())
        logging.basicConfig(filename='../logs/craigslist_{}.log'.format(check_point), level = logging.DEBUG,
            format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
        storage_path = '../data/craigslist/{}/'.format(keyword)
        try:
            os.makedirs('../data/craigslist/{}/dicts'.format(keyword))
            os.makedirs('../data/craigslist/{}/htmls'.format(keyword))
        except OSError, e:
            if e.errno != 17:
                raise

        for city in city_list_sub:
            url_query = url_patt.format(city, keyword)
            item_list = itemsfromAmazonSERP(url_query, city)
            total = len(item_list)
            logging.info("="*20)
            logging.info('collecting {} from {} ...'.format(keyword, city))
            for i, item in enumerate(item_list):
                logging.info('{}/{} processed'.format(i+1, total))
                getInfofromAmazon(item, src='url', city_name=city, storage_path=storage_path)
                if (i+1) % 100 == 0:
                    time.sleep(900)

if __name__ == '__main__':
    main()
