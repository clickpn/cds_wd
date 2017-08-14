#! /usr/bin/env python

import tensorflow as tf
import numpy as np
import pandas as pd
import os
import time
import datetime
import utils
from model_embs import TextCNN
from tensorflow.contrib import learn

# Parameters
# ==================================================

# Data loading params
tf.flags.DEFINE_string("train_dir", "/work/ceb545/models/supp_files/itemtype/cnn.train", "train dir")
tf.flags.DEFINE_string("test_dir", "/work/ceb545/models/supp_files/itemtype/cnn.test", "test dir")
tf.flags.DEFINE_string("val_dir", "/work/ceb545/models/supp_files/itemtype/cnn.val", "val dir")
tf.flags.DEFINE_string("emb_path", "/work/ceb545/models/supp_files/glove.6B.100d.txt",\
        "Path to word embeddings")
tf.flags.DEFINE_string("labels_map_out", "labels_map.dict", "labels mappnig file")
tf.flags.DEFINE_string("save_dir", None, "save dir")

# Model Hyperparameters
tf.flags.DEFINE_integer("embedding_dim", 50, "Dimensionality of character embedding (default: 128)")
tf.flags.DEFINE_string("filter_sizes", "2,3", "Comma-separated filter sizes (default: '3,4,5')")
tf.flags.DEFINE_integer("num_filters", 50, "Number of filters per filter size (default: 128)")
tf.flags.DEFINE_float("dropout_keep_prob", 0.5, "Dropout keep probability (default: 0.5)")
tf.flags.DEFINE_float("l2_reg_lambda", 0.000001, "L2 regularization lambda (default: 0.0)")
tf.flags.DEFINE_float("lr", 5e-4, "Learning Rate")

# Training parameters
tf.flags.DEFINE_integer("batch_size", 64, "Batch Size (default: 64)")
tf.flags.DEFINE_integer("vocab_freq", 10, "Batch Size (default: 64)")
tf.flags.DEFINE_integer("num_epochs", 100, "Number of training epochs (default: 200)")
tf.flags.DEFINE_integer("evaluate_every", 100, "Evaluate model on dev set after this many steps (default: 100)")
tf.flags.DEFINE_integer("checkpoint_every", 100, "Save model after this many steps (default: 100)")
# Misc Parameters
tf.flags.DEFINE_boolean("allow_soft_placement", True, "Allow device soft device placement")
tf.flags.DEFINE_boolean("log_device_placement", False, "Log placement of ops on devices")
tf.flags.DEFINE_boolean("use_sgd", False, "Use sgd or Adam?")
tf.flags.DEFINE_boolean("use_test", False, "Use test data to train? --> For final model")

FLAGS = tf.flags.FLAGS
FLAGS._parse_flags()
print("\nParameters:")
for attr, value in sorted(FLAGS.__flags.items()):
    print("{}={}".format(attr.upper(), value))
print("")


# Data Preparatopn
# ==================================================

# Output directory for models and summaries
if FLAGS.save_dir is None:
    timestamp = str(int(time.time()))
    out_dir = os.path.abspath(os.path.join(os.path.curdir, "runs_itemtype_embs", timestamp))
else:
    out_dir = os.path.abspath(FLAGS.save_dir)
print("Writing to {}\n".format(out_dir))
checkpoint_dir = os.path.abspath(os.path.join(out_dir, "checkpoints"))
checkpoint_prefix = os.path.join(checkpoint_dir, "model")
if not os.path.exists(checkpoint_dir):
    os.makedirs(checkpoint_dir)

print("Loading data...")
x_train,y_train,id_train = utils.\
        load_data(FLAGS.train_dir,labels_map_out=\
        os.path.join(checkpoint_dir,'..',FLAGS.labels_map_out))
if FLAGS.use_test:
    x_supp,y_supp,id_supp = utils.\
            load_data(FLAGS.test_dir,labels_map_out=\
            os.path.join(checkpoint_dir,'..',FLAGS.labels_map_out))
    x_train,y_train,id_train = pd.concat([x_train,x_supp]),pd.concat([y_train,y_supp]),\
            pd.concat([id_train,id_supp])
x_dev,y_dev,ids_dev = utils.\
        load_data(FLAGS.val_dir, labels_map_out=\
        os.path.join(checkpoint_dir,'..',FLAGS.labels_map_out))
y_train = utils.arrify_labels(y_train)
y_dev = utils.arrify_labels(y_dev)
# Build vocabulary
max_document_length = max([len(x.split(" ")) for x in x_train])
vocab_processor = learn.preprocessing.VocabularyProcessor(max_document_length,\
        min_frequency=FLAGS.vocab_freq)
x_train = np.array(list(vocab_processor.fit_transform(x_train)))
x_dev = np.array(list(vocab_processor.transform(x_dev)))
embeddings = utils.load_embeddings(FLAGS.emb_path, vocab_processor)
print(embeddings)
shuf_train = np.random.permutation(np.arange(len(x_train)))
shuf_dev = np.random.permutation(np.arange(len(x_dev)))
x_train,y_train = x_train[shuf_train],y_train[shuf_train]
x_dev,y_dev = x_dev[shuf_dev],y_dev[shuf_dev]

val_accs = []


# Training
# ==================================================

with tf.Graph().as_default():
    session_conf = tf.ConfigProto(
      allow_soft_placement=FLAGS.allow_soft_placement,
      log_device_placement=FLAGS.log_device_placement)
    sess = tf.Session(config=session_conf)
    embedding_size = embeddings.shape[1]
    with sess.as_default():
        cnn = TextCNN(
            sequence_length=x_train.shape[1],
            num_classes=y_train.shape[1],
            vocab_size=len(vocab_processor.vocabulary_),
            embedding_size=embedding_size,
            filter_sizes=list(map(int, FLAGS.filter_sizes.split(","))),
            num_filters=FLAGS.num_filters,
            l2_reg_lambda=FLAGS.l2_reg_lambda)

        # Define Training procedure
        global_step = tf.Variable(0, name="global_step", trainable=False)
        if FLAGS.use_sgd:
            optimizer = tf.train.GradientDescentOptimizer(FLAGS.lr)
        else:
            optimizer = tf.train.AdamOptimizer(FLAGS.lr)
        grads_and_vars = optimizer.compute_gradients(cnn.loss)
        train_op = optimizer.apply_gradients(grads_and_vars, global_step=global_step)

        # Keep track of gradient values and sparsity (optional)
        grad_summaries = []
        for g, v in grads_and_vars:
            if g is not None:
                grad_hist_summary = tf.histogram_summary("{}/grad/hist".format(v.name), g)
                sparsity_summary = tf.scalar_summary("{}/grad/sparsity".format(v.name), tf.nn.zero_fraction(g))
                grad_summaries.append(grad_hist_summary)
                grad_summaries.append(sparsity_summary)
        grad_summaries_merged = tf.merge_summary(grad_summaries)


        # Summaries for loss and accuracy
        loss_summary = tf.scalar_summary("loss", cnn.loss)
        acc_summary = tf.scalar_summary("accuracy", cnn.accuracy)

        # Train Summaries
        train_summary_op = tf.merge_summary([loss_summary, acc_summary, grad_summaries_merged])
        train_summary_dir = os.path.join(out_dir, "summaries", "train")
        train_summary_writer = tf.train.SummaryWriter(train_summary_dir, sess.graph)

        # Dev summaries
        dev_summary_op = tf.merge_summary([loss_summary, acc_summary])
        dev_summary_dir = os.path.join(out_dir, "summaries", "dev")
        dev_summary_writer = tf.train.SummaryWriter(dev_summary_dir, sess.graph)

        saver = tf.train.Saver(tf.all_variables())

        # Write vocabulary
        vocab_processor.save(os.path.join(out_dir, "vocab"))

        # Initialize all variables
        #sess.run(tf.global_variables_initializer())
        sess.run(tf.initialize_all_variables())

        def train_step(x_batch, y_batch):
            """
            A single training step
            """
            feed_dict = {
              cnn.input_x: x_batch,
              cnn.input_y: y_batch,
              cnn.W_emb: embeddings,
              cnn.dropout_keep_prob: FLAGS.dropout_keep_prob
            }
            _, step, summaries, loss, accuracy = sess.run(
                [train_op, global_step, train_summary_op, cnn.loss, cnn.accuracy],
                feed_dict)
            time_str = datetime.datetime.now().isoformat()
           # print("{}: step {}, loss {:g}, acc {:g}".format(time_str, step, loss, accuracy))
            train_summary_writer.add_summary(summaries, step)

        def dev_step(x_batch, y_batch, writer=None):
            """
            Evaluates model on a dev set
            """
            feed_dict = {
              cnn.input_x: x_batch,
              cnn.input_y: y_batch,
              cnn.W_emb: embeddings,
              cnn.dropout_keep_prob: 1.0
            }
            step, summaries, loss, accuracy,scores = sess.run(
                [global_step, dev_summary_op, cnn.loss, cnn.accuracy,cnn.scores],
                feed_dict)
            print(scores)
            time_str = datetime.datetime.now().isoformat()
            print("{}: step {}, loss {:g}, acc {:g}".format(time_str, step, loss, accuracy))
            if writer:
                writer.add_summary(summaries, step)
            return accuracy

        # Generate batches
        batches = utils.batch_iter(
            list(zip(x_train, y_train)), FLAGS.batch_size, FLAGS.num_epochs)
        # Training loop. For each batch...
        for batch in batches:
            x_batch, y_batch = zip(*batch)
            train_step(x_batch, y_batch)
            current_step = tf.train.global_step(sess, global_step)
            if current_step % FLAGS.evaluate_every == 0:
                print("\nEvaluation:")
                acc = dev_step(x_dev, y_dev, writer=dev_summary_writer)
                if len(val_accs) > 0:
                    if (acc > max(val_accs)):
                        path = saver.save(sess, os.path.join(checkpoint_dir,'best_model'))
                        print("Achieved maximum val accuracy..saving model to %s"%path)
                val_accs.append(acc)
                if((len(val_accs) > 10)&((max(val_accs[-10:])<max(val_accs)))):
                    break
                print("")
            if current_step % FLAGS.checkpoint_every == 0:
                path = saver.save(sess, checkpoint_prefix, global_step=current_step)
                print("Saved model checkpoint to {}\n".format(path))
tf.reset_default_graph()
utils.save_model(os.path.join(checkpoint_dir,'best_model'))
