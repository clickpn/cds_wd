#! /usr/bin/env python

import tensorflow as tf
from tensorflow.python.platform import gfile
import numpy as np
import pickle
import pandas as pd
import os
import utils
import json
import csv
from tensorflow.contrib import learn

tf.flags.DEFINE_string("test_data", \
	"../model_data/unlabeled_db.csv",
        "Location of test data")
tf.flags.DEFINE_boolean("save", \
        False, \
        "Should you save output of model")
tf.flags.DEFINE_integer("batch_size", 32, "Batch size")
tf.flags.DEFINE_string("rel_dir",\
        "./rel_model"\
        , "Directory where relevance model is saved")
tf.flags.DEFINE_string("it_dir",\
        "./it_model"\
        , "Directory where item type model is saved")

FLAGS = tf.flags.FLAGS
FLAGS._parse_flags()

def softmax(row):
    row = [np.exp(x) for x in row]
    row_sum = sum(row)
    row = [x/row_sum for x in row]
    return row

def create_graph(model_filename):
  """"Creates a graph from saved GraphDef file.
  """
  tf.reset_default_graph()
  print("Loading model..")
  with tf.Session() as sess:
    with gfile.FastGFile(model_filename, 'rb') as f:
      graph_def = tf.GraphDef()
      graph_def.ParseFromString(f.read())
      tf.import_graph_def(graph_def, name='', return_elements=[
              'output/predictions'])
  return sess.graph

def get_results(model_dir):

	x_raw,y_test,ids_test = utils.load_data(FLAGS.test_data,labels_map_out=\
		os.path.join(model_dir,'labels_map.dict'))
	vocab_path = os.path.join(model_dir, "vocab")
	vocab_processor = learn.preprocessing.VocabularyProcessor.restore(vocab_path)
	x_test = np.array(list(vocab_processor.transform(x_raw)))

	model_path = os.path.join(model_dir,"best_model.pb")

	# load mapping of labels
	mapping = pickle.load(open(os.path.join(model_dir,'labels_map.dict')))
	rev_mapping = {v:k for k,v in mapping.iteritems()}

	print("\nEvaluating...\n")

	graph = create_graph(model_path)
	sess = tf.Session()
	init = tf.global_variables_initializer()
	sess.run(init)
	input_x = sess.graph.get_tensor_by_name('input_x:0')
	dropout_keep_prob = sess.graph.get_tensor_by_name('dropout_keep_prob:0')
	predictions = sess.graph.get_tensor_by_name('output/predictions:0')
	scores = sess.graph.get_tensor_by_name('output/scores:0')

	# Batch data
	batches = utils.batch_iter(list(x_test), FLAGS.batch_size, 1, shuffle=False)

	# Collect predictions
	all_predictions = []
	all_scores = []


	for batch in batches:
	    batch_predictions = sess.run(predictions, feed_dict={input_x: batch, dropout_keep_prob: 1.0})
	    batch_scores = sess.run(scores, feed_dict={input_x: batch, dropout_keep_prob: 1.0})
	    if 'true' in mapping:
		batch_scores = [softmax(x)[mapping['true']] for x in batch_scores]
	    else:
		batch_scores = [max(softmax(x)) for x in batch_scores]
	    all_predictions = np.concatenate([all_predictions, batch_predictions])
	    all_scores = np.concatenate([all_scores,batch_scores])

	# Map to string labels
	mapped_predictions = [rev_mapping[int(x)] for x in all_predictions]
	predictions_human_readable = np.column_stack((np.array(x_raw), mapped_predictions))
	predictions_human_readable = np.insert(predictions_human_readable,0,ids_test,axis=1)
	if y_test is not None:
	    mapped_labels = [rev_mapping[int(x)] for x in y_test]
	    match = [1 if x==y else 0 for x,y in zip(mapped_predictions,mapped_labels)]
	    tp = [1 for x,y in zip(match,mapped_predictions) if x==1 and y=='true']
	    tn = [1 for x,y in zip(match,mapped_predictions) if x==1 and y=='false']
	    fp = [1 for x,y in zip(match,mapped_predictions) if x==0 and y=='true']
	    fn = [1 for x,y in zip(match,mapped_predictions) if x==0 and y=='false']
	    precision = float(len(tp))/(len(tp)+len(fp))
	    recall = float(len(tp))/(len(tp)+len(fn))
	    print("PRECISION: %.3f; RECALL: %.3f"%(precision,recall))
	    predictions_human_readable = np.insert(predictions_human_readable,0,\
		    mapped_labels,axis=1)
	    print("Total number of test examples: {}".format(len(y_test)))
	    print("Accuracy: {:g}".format(float(sum(match))/float(len(y_test))))
	return mapped_predictions,all_scores

if __name__=="__main__":

	dataset = pd.read_csv(FLAGS.test_data)
	it_pred,it_scores = get_results(FLAGS.it_dir)
	rel_pred,rel_scores = get_results(FLAGS.rel_dir)
	print("\nLoading data from %s"%FLAGS.test_data)
	# Compare against labels, if available
	if FLAGS.save:
	    dataset['rel_predictions'] = rel_pred
	    dataset['rel_scores'] = rel_scores
	    dataset['item_predictions'] = it_pred
	    dataset['item_scores'] = it_scores
	    dataset.to_csv(FLAGS.test_data,index=False)
