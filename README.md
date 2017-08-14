# WD project README
## Note: 
1. Change revelant directory path such as keyword list input path
2. Delete all hidden .DS_store file
3. KW list can be downloaded from Dropbox


## Directory Explaination
1. craig_hpc: contains code for craigslist
2. model: contains code for NLP model and model_pipeline.py
3. pipeline: contains process from processing data, prediction, input to MongoDB and output as json format

## Usage
### pipeline
1. run `python main.py`. 
Note: Change line 24 into dir_path you want.
It will take original format dicts from '/search_by_kw/data/{}/dicts' and then modify the format.
Meanwhile, it will create a local connection to MongoDB and import data into MongoDB
Finally, it will generate csv file for model input.

2. run `bash generate_score.sh`
Note: change dir_path 'cd ../model'
It will update csv file with relevant score and item type by using saved model file.

3. run `python priority_adj.py`. 
It will adjust model results based on additional high priority keyword and low priority keyword.

4. run `python export_example.py`
it will update data in MongoDB and output 100 examples json files which rel_score is greater than 0.8. You can adjust search query in pyMongo to fullfill you custom request.

