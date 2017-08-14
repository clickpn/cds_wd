import ca_db_script as dbs
import pandas as pd
from pymongo import MongoClient
import pickle
import kw_format_correct as fc
import os
import re
import json

# update mongoDB
def main():
    # import data
    kws_list = pickle.load(open('CA_kws.p'))
    csv_path_patt = './csv_file/{}.csv'

    for kw in kws_list:
        csv_path = csv_path_patt.format(kw)
        con = dbs.connect_site()
        dataset = pd.read_csv(csv_path)
        dbs.update_data(dataset, con)

        # output 100 examples into json
        # cursor = con.find({'label':{'$gt':0.8}, 'search_term': kw}).limit(100).sort('price')
        # cursor = con.find({'label.rel_score': {'$gt': 0.8}, 'price_info.price': {'$gt': 0.1}, 'search_term': kw}).limit(300).sort('price')
        cursor = con.find({'price_info.price': {'$gt': 0.1}, 'search_term': kw}).limit(300).sort('price')
        output = list(cursor)
        json.dump(output, open('./json_file/{}.json'.format(kw), 'wb'))
        # with open('./json_file/{}.json'.format(kw), 'wb') as f:
        #     for i in output:
        #         f.write(json.dumps(i) + '\n')

if __name__ == '__main__':
    main()

# with open('abalone.json', 'w') as f:
#     for i in output:
#         f.write(json.dumps(i) + '\n')
