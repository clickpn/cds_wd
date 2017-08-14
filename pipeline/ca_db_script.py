from pymongo import MongoClient
import pandas as pd
import os
import pickle
"""
Scripts for accessing MongoDB database of site records
"""

def connect_site():
    client = MongoClient()
    db = client.wildca
    collection = db.query_data
    return collection

def load_data(fns, collection):
    # fns = [os.path.join(pa,x) for x in os.listdir(pa) if 'dict' in x]
    # fns = [pickle.load(open(x)) for x in fns]
    cnt=0
    for f in fns:
        if not collection.find_one({'_id.id':f['_id']['id'],'_id.site':f['_id']['site']}):
            cnt+=1
            # print f['date_searched']
            collection.insert_one(f)

def find_labeled(c):
    return c.find({'label':{'$ne':None}})

def update_data(labeled,collection):
    """
    Update data with predictions (designed for artifacts..can be used more generally?)
    columns needed: ['id','site','predictions']
    """
    labeled_dict = labeled.to_dict(orient='records')

    db_dict = [{'_id':{u'id':x['id'],u'site':x['site']},'label':{'old_rel_score': x['old_scores'], 'rel_score': x['rel_scores']}, \
            'artifacts':x['item_predictions']} \
            for x in labeled_dict]

    for f in db_dict:
        collection.update_one({'_id.id':str(f['_id']['id']).decode('utf-8'),'_id.site':str(f['_id']['site']).decode("utf-8")},\
                {'$set':{'label':f['label'],'artifacts':f['artifacts']}})


def extract_unlabeled(collection,out_path=None):
    """
    Extract artifacts without labels from DB and
    (optionally) save to file
    """
    need_preds = list(collection.find({'artifacts':None,'label':None}))
    print("Found %s items with missing values"%(len(need_preds)))
    alt_preds = [[x['_id']['id'],x['_id']['site'],x['title']] for x in need_preds]
    alt_preds_df = pd.DataFrame(alt_preds)
    if len(alt_preds_df) == 0:
        print("Nothing unlabeled found")
        if out_path is not None:
            if os.path.exists(out_path):
                os.remove(out_path)
        return None
    alt_preds_df.columns = ['id','site','text']
    if out_path is not None:
        print("Saving extracted info to %s"%out_path)
        alt_preds_df.to_csv(out_path,index=False,encoding='utf-8')
    return alt_preds_df

if __name__=='__main__':
    sd = connect_site()
    print("# records: %s\n"%len(list(sd.find({'_id.site':'etsy'}))))
    up_lab_path = '/home/ceb545/wildlife/clean_data/labeled_art.csv'
    update_data(up_lab_path,sd,field='artifacts')
    up_lab_path = '/home/ceb545/wildlife/clean_data/labeled_label.csv'
    update_data(up_lab_path,sd,field='label')
    example_record = sd.find_one()
    print("example record:\n\n%s"%example_record)
