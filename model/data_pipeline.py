import db_script as dbs
import model_pipeline
import pandas as pd
from pymongo import MongoClient
import pickle

# modified by Sida

data_path = '/Users/sidaye/Desktop/wildlife_model/sida_code/ebay_data.csv'
con = dbs.connect_site()
# dbs.extract_unlabeled(con, out_path=data_path)
dataset = pd.read_csv(data_path)

# it_pred, _ = model_pipeline.get_results(model_pipeline.FLAGS.it_dir)
# _, rel_scores = model_pipeline.get_results(model_pipeline.FLAGS.rel_dir)
# print("\nLoading data from %s"%model_pipeline.FLAGS.test_data)
# # Compare against labels, if available

# dataset['rel_scores'] = rel_scores
# dataset['item_predictions'] = it_pred

dbs.update_data(dataset, con)

# sample test to print random one record in MongoDB
# import pprint
client = MongoClient()
db = client.wildlife
collection = db.site_data
# pprint.pprint(collection.find_one())

### find 100 examples with label > 0.8
# collection.find_one({'_id.id': u'110832420693'})
# db.collection.find( { qty: { $gt: 4 } } )
for record in collection.find({'label':{'$gt':0.8}}):
    while i < 11:
        print record
        i += 1

cursor = collection.find({'label':{'$gt':0.8}})
cursor.count()
cursor = collection.find({'label':{'$gt':0.8}}).limit(100).sort('price')
print cursor.count(with_limit_and_skip=True)

# save subset of MongoDB collection to another collection
# db.full_set.aggregate([ { $match: { date: "20120105" } }, { $out: "subset" } ])
collection.aggregate([{'$match': {'label':{'$gt':0.8}}},
    {'$limit': 100},
    {'$out': 'subset'}])

# export collection to json
# bash
# mongoexport --db wildlife --collection subset --out ebay_sample.json

# load json
import json
with open('ebay_sample.json') as data_file:
    data = json.load(data_file)

data = []
with open('ebay_sample.json') as f:
    for line in f:
       data.append(json.loads(line))

