import ca_db_script as dbs
import pandas as pd
from pymongo import MongoClient
import pickle
import kw_format_correct as fc
import os
import re
import json


# generate csv file for model
def generate_csv(data, output_path):
    columns = ['id', 'site', 'text']
    d = [[p['_id']['id'], p['_id']['site'], p['title']] for p in data]
    df = pd.DataFrame(d, columns=columns)
    try:
        df.to_csv(output_path, sep=',', header=True, encoding='utf-8', index=False)
    except UnicodeEncodeError:
        pass

def main():
    # import data
    kws_list = pickle.load(open('CA_kws.p'))
    data_path_patt = '../search_by_kw/data/{}/dicts'

    for kw in kws_list:
        data_path = data_path_patt.format(kw)
        # correct format
        fns = [os.path.join(data_path, x) for x in os.listdir(data_path) if 'dict' in x]
        fns = [pickle.load(open(x)) for x in fns]
        fns = [fc.modify_format(x, kw) for x in fns]

        # import to MongoDB
        con = dbs.connect_site()
        dbs.load_data(fns, con)

        # generate csv file
        generate_csv(fns, './csv_file/{}.csv'.format(kw))

if __name__ == '__main__':
    main()
