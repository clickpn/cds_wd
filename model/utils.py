import numpy as np
from tensorflow.python.framework import graph_util
import tensorflow as tf
import pickle
import os
import pandas as pd
import re
import itertools
from collections import Counter


def clean_str(string):
    """
    Tokenization/string cleaning for all datasets except for SST.
    Original taken from https://github.com/yoonkim/CNN_sentence/blob/master/process_data.py
    """
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"\'s", "", string)
    string = re.sub(r"\'ve", "", string)
    string = re.sub(r"n\'t", "", string)
    string = re.sub(r"\'re", "", string)
    string = re.sub(r"\'d", "", string)
    string = re.sub(r"\'ll", "", string)
    #string = re.sub(r",", " , ", string)
    #string = re.sub(r"!", " ! ", string)
    #string = re.sub(r"\(", " \( ", string)
    #string = re.sub(r"\)", " \) ", string)
    #string = re.sub(r"\?", " \? ", string)
    string = re.sub(r"\s{2,}", " ", string)
    string = re.sub(r"[0-9(),!?\'\`]", "", string)
    string = re.sub(r"\s{2,}", " ", string)
    return string.strip().lower()

def load_embeddings(path,vocab):
    embs = ([x.split(" ") for x in open(path).read().strip().split("\n")])
    words = np.array([x[0] for x in embs])
    mat = np.array([x[1:] for x in embs]).astype(float)
    mapped_words = [x[0] for x in vocab.transform(words)]
    vocab_size = len(vocab.vocabulary_)
    emb_matrix = np.zeros((vocab_size,mat.shape[1]))
    set_words = set(mapped_words)
    for i in range(vocab_size):
        if i in set_words:
            emb_matrix[i]=mat[mapped_words.index(i)]
    return emb_matrix


def load_all_cap_data(cap_path='/scratch/ceb545/wrk/info_files/caption_meta.csv'):
    all_captions = pd.read_csv(cap_path)
    all_captions.text = all_captions.text.apply(lambda x: clean_str(x))
    return all_captions.text, all_captions.id

def load_data(data_path,labels_map_out=None):
    """
    Load data from a csv of columns id, text, and (optionally) labels
    """
    data = pd.read_csv(data_path,dtype=str)
    data.id = data.id.apply(lambda x: str(x))
    data.text = data.text.apply(lambda x: clean_str(x))
    if os.path.isfile(labels_map_out):
        print("Loading labels mapping from %s"%labels_map_out)
        labels_mapping = pickle.load(open(labels_map_out))
    elif ('label' in data.columns):
        labels_mapping = {x:i for i,x in enumerate(list(set(data['label'])))}
        print('saving labels mapping to %s'%labels_map_out)
        pickle.dump(labels_mapping,open(labels_map_out,'w'))
        
    if (os.path.isfile(labels_map_out)& ('label' in data.columns)):
        print("Loading labels mapping from %s"%labels_map_out)
        labels_mapping = pickle.load(open(labels_map_out))
        data.label = data.label.apply(lambda x: labels_mapping[x])
        return data.text, data.label, data.id

    else:
        print("Loading data without labels")
        return data.text, None, data.id

def arrify_labels(labels):
    array_labels = np.zeros((len(labels),len(labels.unique())))
    for i, l in enumerate(labels):
        array_labels[i][l]=1
    return array_labels

def load_res_data(dir,labels_map_out='labels_map_rel.dict',\
        cap_path='/scratch/ceb545/wrk/info_files/caption_meta.csv'):
    """
    Loads data from image files located in directories for transfer learning
    """
    label_dirs = [os.path.join(dir,x) for x in os.listdir(dir)]
    if os.path.isfile(labels_map_out):
        print("Loading labels mapping from %s"%labels_map_out)
        labels_mapping_cats = pickle.load(open(labels_map_out))
        labels_mapping = {os.path.join(dir,k):v for k,v in labels_mapping_cats.iteritems()}
    else:
        labels_mapping = {x:i for i,x in enumerate(label_dirs)}
        labels_mapping_cats = {x.split("/")[-1]:i for i,x in enumerate(label_dirs)}
        print('saving labels mapping to %s'%labels_map_out)
        pickle.dump(labels_mapping_cats,open(labels_map_out,'w'))
    all_captions = pd.read_csv(cap_path)
    all_captions.id = all_captions.id.apply(lambda x: str(x))
    all_captions = all_captions.set_index('id')
    all_ids = []
    x_text = []
    y = []
    for di in label_dirs:
        # remove duplicated
        ids = list(set([x.split("_")[0] for x in os.listdir(di)]))
        captions = [all_captions.loc[str(x)].text for x in ids]
        index_label = np.zeros(len(label_dirs))
        index_label[labels_mapping[di]]=1
        mapped_labels = [index_label for i in range(len(ids))]
        x_text.extend(captions)
        all_ids.extend(ids)
        y.extend(mapped_labels)

    
    x_text = [clean_str(sent) for sent in x_text]
    x_text = np.array(x_text)
    y = np.array(y)
    all_ids = np.array(all_ids)
    assert(sum([len(x_text),len(y),len(all_ids)])/3 == len(x_text))
    return [x_text, y,all_ids]



def load_data_and_labels(positive_data_file, negative_data_file):
    """
    Loads MR polarity data from files, splits the data into words and generates labels.
    Returns split sentences and labels.
    """
    # Load data from files
    positive_examples = list(open(positive_data_file, "r").readlines())
    positive_examples = [s.strip() for s in positive_examples]
    negative_examples = list(open(negative_data_file, "r").readlines())
    negative_examples = [s.strip() for s in negative_examples]
    # Split by words
    x_text = positive_examples + negative_examples
    x_text = [clean_str(sent) for sent in x_text]
    # Generate labels
    positive_labels = [[0, 1] for _ in positive_examples]
    negative_labels = [[1, 0] for _ in negative_examples]
    y = np.concatenate([positive_labels, negative_labels], 0)
    return [x_text, y]


def save_model(input_graph_path):
    """
    Serialize saved TensorFlow graph checkpoint
    """
    input_graph_path = os.path.abspath(input_graph_path)
    checkpoint_dir = os.path.dirname(input_graph_path)

    # if cant find that specific graph, try saving latest checkpoint
    if not os.path.exists(input_graph_path+'.meta'):
        print("Couldn't find graph. Saving recent checkpoint instead.")
        input_graph_path = tf.train.latest_checkpoint(checkpoint_dir)
    saver = tf.train.import_meta_graph(input_graph_path + '.meta', clear_devices=True)
    graph = tf.get_default_graph()
    input_graph_def = graph.as_graph_def()
    serialized_path = os.path.abspath(os.path.join(checkpoint_dir,'..',"best_model.pb"))

    with tf.Session() as sess:
        # restore checkpoint
        print("Loading graph from %s"%input_graph_path)
        saver.restore(sess, input_graph_path)
        # freeze graph until predictions node
        serialized_path_def = graph_util.convert_variables_to_constants(
            sess,
            input_graph_def,
            ["output/predictions"])

        with tf.gfile.GFile(serialized_path, "wb") as f:
            f.write(serialized_path_def.SerializeToString())
        print("Saved serialized graph to %s"%serialized_path)


def batch_iter(data, batch_size, num_epochs, shuffle=True):
    """
    Generates a batch iterator for a dataset.
    """
    data = np.array(data)
    data_size = len(data)
    num_batches_per_epoch = int((len(data)-1)/batch_size) + 1
    for epoch in range(num_epochs):
        # Shuffle the data at each epoch
        if shuffle:
            shuffle_indices = np.random.permutation(np.arange(data_size))
            shuffled_data = data[shuffle_indices]
        else:
            shuffled_data = data
        for batch_num in range(num_batches_per_epoch):
            start_index = batch_num * batch_size
            end_index = min((batch_num + 1) * batch_size, data_size)
            yield shuffled_data[start_index:end_index]
