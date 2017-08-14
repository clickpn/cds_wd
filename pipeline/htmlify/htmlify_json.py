import json
import pprint
import pickle as cp
import time
import os
import sys
from bs4 import BeautifulSoup as bs
import urllib2 as u
import traceback
import argparse
import re
from os.path import isfile, join

"""
This file is to create display page from json data (7/1/2017)
"""

parser = argparse.ArgumentParser(description='htmlify')
parser.add_argument('--data', type=str, default='../json_file/elephant.json',
                    help='path')
args = parser.parse_args()

storage_path = args.data

def htmlheader():
    t1=""
    t2=""


    with open('template1.txt') as file:
        t1 = file.read()

    return t1

def htmlfooter():
    foot = ''
    # foot = "\n</div>\n<button type=\"button\" onclick=\"save()\">Save</button>\n"
    # foot += '<p id="op"></p>\n'
    foot += '<script>\nvar info = [];\nfunction save(m,usid) {\n window.location.href = "savedata.py?uid="+usid+"&id="+m+"&rel="+document.getElementById("rel"+m).value+"&species="+document.getElementById("tp"+m).value+"<>"+document.getElementById("subtp"+m).value+"&species2="+document.getElementById("tp2"+m).value+"<>"+document.getElementById("subtp2"+m).value+"&artefact="+document.getElementById("art"+m).value+"<>"+document.getElementById("subart"+m).value;\n}\n'

    foot += 'function enume(id) {\n var vl = document.getElementById(id).selectedIndex;\
    document.getElementById("sub"+id).options.length = 0;\
    var cat =[ ["Coats","Shoes","Pants","Dress","Shirts","Other"], ["Jewelry","Belt","Purse_bags","Hat","Other"], ["Taxidermy","Skin","Bone_ivory","Tooth","Other"],["Furniture","Rug","Other"]];\
    for (var i= 0;  i < cat[vl].length ; i++) {\
    var x = document.getElementById("sub"+id);\n\
    var option = document.createElement("option");\n\
    option.text = cat[vl][i];\n\
    x.add(option);\n}\n\
    }'
    foot += 'function enumesp(id) {\n   var vl = document.getElementById(id).selectedIndex;\
    document.getElementById("sub"+id).options.length = 0;\
    var sptpcat = [["Antelope/deer/camel/hippopotamus","Zebra/rhino/tapir/horse","Carnivore (big-cat,bears,weasels,seals etc)","Whale/dolphin/porpoise","Bat","Pangolin","Primate (apes, monkey, lemures etc.)","Rodent","Elephant, mastodon","Manatee, dugong","Other"], ["parrots/ macaws","Falcon","owl","toucans,woodpeckers","other"], ["Shark/ray/sawfish","Other"], ["Turtles, tortoises, terrapins","Lizards, snakes","Crocodiles, alligators, caimans","Other"], ["Frog/Toad","Other"], ["crabs/lobsters","seastar, sea urchin, sea cucumber","octopus, clams, oysters, abalone","snails","corals","other"]];\
    for (var i= 0;  i < sptpcat[vl].length ; i++) {\
    var x = document.getElementById("sub"+id);\n\
    var option = document.createElement("option");\n\
    option.text = sptpcat[vl][i];\n\
    x.add(option);\n}\n\
    }'
    foot += 'function enumesp2(id) {\n   var vl = document.getElementById(id).selectedIndex;\
    document.getElementById("sub"+id).options.length = 0;\
    var sptpcat = [[" "], ["Antelope/deer/camel/hippopotamus","Zebra/rhino/tapir/horse","Carnivore (big-cat,bears,weasels,seals etc)","Whale/dolphin/porpoise","Bat","Pangolin","Primate (apes, monkey, lemures etc.)","Rodent","Elephant, mastodon","Manatee, dugong","Other"], ["parrots/ macaws","Falcon","owl","toucans,woodpeckers","other"], ["Shark/ray/sawfish","Other"], ["Turtles, tortoises, terrapins","Lizards, snakes","Crocodiles, alligators, caimans","Other"], ["Frog/Toad","Other"], ["crabs/lobsters","seastar, sea urchin, sea cucumber","octopus, clams, oysters, abalone","snails","corals","other"]];\
    for (var i= 0;  i < sptpcat[vl].length ; i++) {\
    var x = document.getElementById("sub"+id);\n\
    var option = document.createElement("option");\n\
    option.text = sptpcat[vl][i];\n\
    x.add(option);\n}\n\
    }'
    foot += '</script>'
    foot += "</body>\n</html>"
    return foot


def htmlify(res, uid):
    id = res['_id']['id']
    with open('template_img.txt') as file:
       t2 = file.read()

    tmp = ''
#    if True:
    try:
        tmp = tmp + '<table>\n<tr>\n'
        tmp = tmp + '<td><a href = "'+res['url']+'"><h3><b>'+res['title']+'</b></h3></a><h3>(ID:'+str(id)+')</h3></td>\n</tr></table>'
#        tmp = tmp + '<td><h3><b>'+res['title']+'</b></h3></td>\n</tr></table>'

        tmp=tmp+'<table class="table table-hover">\n<tr>\n'
        # for i,k in enumerate(res['images'][3:9]):
        for i,k in enumerate(res['image_urls']):
            if i%5==0 and i>0:
                tmp=tmp+'</tr>\n<tr>\n'
            # if k[:4]!='http':
            #     continue#k='http:'+k
            if 'maxImageUrl' in k:
                tmp = tmp + t2.replace('<img_src>',k['maxImageUrl']).replace('<img_href>',k['maxImageUrl'])
            else:
                tmp = tmp + t2.replace('<img_src>',k).replace('<img_href>',k)

        tmp += '</tr>\n</table>\n'

        if res['price_info']['price'] != -1:
            price = float(res['price_info']['price'])
        else:
            price = 0.0

        # #### ebay only #####
        # price = res['price']
        # ############
        if price != 0.0:
            tmp += 'Price: USD %.2f <br>'%price
        else:
            tmp += 'Price: Sold Out <br>'
        tmp += 'Source: %s'%res['_id']['site']
        # tmp += 'Item location: %s <br>'%res['shipping_info']['item_location'][0]
        # tmp += 'Shipped to: %s <br>'%res['shipping_info']['posts_to'][0]
        # tmp += 'Seller: <a href="%s">%s</a><br>'%(res['seller']['url'],res['seller']['name'])
        # if len(res['description_links'])>0:
        #     tmp += '<a href="%s">More details</a>'%res['description_links'][0]

        # tmp += '\n<br> Relevance (Whether the item displayed is an animal/wildlife product): <select name="relv" id="rel'+str(id)+'" onchange="relv(id)">\
        # <option value="relevant">Relevant</option>\
        # <option value="irrelevant">Irrelevant</option>\
        # </select>'
        # tmp += '\n<br> Animal type: <select name="types" id="tp'+str(id)+'" onchange="enumesp(id)">\
        # <option value="mammal">Mammals</option>\
        # <option value="bird">Bird</option>\
        # <option value="fish">Fish</option>\
        # <option value="reptile">Reptile</option>\
        # <option value="amphibian">Amphibian</option>\
        # <option value="invertebrate">Invertebrate</option>\
        # <option value="invertebrate">Irrelevant</option>\
        # </select>'
        # tmp += '\n<select name="subtp" id="subtp'+str(id)+'">\
        # <option value="even">Antelope/deer/camel/hippopotamus</option>\
        # <option value="odd">Zebra/rhino/tapir/horse</option>\
        # <option value="carnivores">Carnivore (big-cat,bears,weasels,seals etc)</option>\
        # <option value="marine">Whale/dolphin/porpoise</option>\
        # <option value="bat">Bat</option>\
        # <option value="pangolin">Pangolin</option>\
        # <option value="primate">primate (apes,monkey, lemur etc.)</option>\
        # <option value="rodent">Rodent</option>\
        # <option value="tusk">Elephant,mastodon</option>\
        # <option value="sirenians">Manatee,dugong</option>\
        # <option value="other">Other</option></select>'
        # tmp += '\nSecond Animal type (if any): <select name="types" id="tp2'+str(id)+'" onchange="enumesp2(id)">\
        # <option value="blank"> </option>\
        # <option value="mammal">Mammals</option>\
        # <option value="bird">Bird</option>\
        # <option value="fish">Fish</option>\
        # <option value="reptile">Reptile</option>\
        # <option value="amphibian">Amphibian</option>\
        # <option value="invertebrate">Invertebrate</option>\
        # <option value="invertebrate">Irrelevant</option>\
        # </select>'
        # tmp += '\n<select name="subtp" id="subtp2'+str(id)+'">\
        # <option value="bl"> </option>\
        # </select>'
        # tmp += '\n<br> Artifact: <select name="species" id="art'+str(id)+'" onchange="enume(id)">\
        # <option value="clothing">Clothing</option>\
        # <option value="accessories">Accessories</option>\
        # <option value="body_parts">Body parts</option>\
        # <option value="home_decor">Home decor</option>\
        # <option value="other">Other</option>\
        # </select>'
        # tmp += '\n<select name="sub" id="subart'+str(id)+'">\
        # <option value="coats">Coats</option>\
        # <option value="shoes">Shoes</option>\
        # <option value="pants">Pants</option>\
        # <option value="dress">Dress</option>\
        # <option value="shirts">Shirts</option></select>'
        
        # tmp += '\n<br>\n <button onclick="save('+id+','+uid+')" type="button">Save</button>'
        # tmp += '<hr size="5" >\n'
    except Exception,e:
        print 'bad'
        print e,'bad'
    return tmp.encode('ascii','ignore')

# def rank(data,key):
#     # Make a list or ranks to be sorted
#     for ad in data:
#         if len(ad[key]) == 0:
#             ad[key] = '0.0'
#     ranks = [x for x in xrange(len(data))]
#     # Sort ranks based on the key of data each refers to
#     # ebay only
#     # for i in data:
#     #     if i[key] == []:
#     #         i[key] = 0
#     #     else:
#     #         i[key] = float(''.join(re.findall(r'\d+', i[key]))) / 100
#     # return sorted(ranks, reverse=True, key=lambda x: data[x][key])
#     return sorted(ranks, reverse=True, key=lambda x: float(''.join(re.findall(r'\d+', data[x][key].split()[0])[:3]))/100)

def rank(data):
    ranks = [x for x in xrange(len(data))]
    return sorted(ranks, reverse=True, key=lambda x: float(str(data[x]['price_info']['price'])))

def toHtml(ads,uid):
    # print htmlheader()
    for ad in ads:
        print htmlify(ad, uid)
    print htmlfooter()

if __name__ == '__main__':
    dict_list = json.load(open(storage_path))
    rank_idx = rank(dict_list)
    ordered_list = [dict_list[i] for i in rank_idx]
    toHtml(ordered_list, '1234')

    # toHtml([cp.load(open(storage_path+file)) for file in os.listdir(storage_path) if isfile(join(storage_path, file))], '1234')

#ADD SAVE CONFIRMATION BY PUTTING THE SAVED RESULTS (READING FROM FILE)

#ids = []
