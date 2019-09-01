# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 16:59:06 2019

@author: Li Xiang

get generated review embbedings
"""

import sys
import h5py
import tensorflow_hub as hub
import tensorflow as tf
import pandas as pd
import numpy as np

df=pd.read_csv("../data/generated_reviews.csv")


all_asins=list(df['asin'].unique())

asin_review=dict()

for _asin in all_asins: 
    asin_review[_asin]=df[df.asin==_asin]['reviews'].tolist()

#--------def functions and get max review length-----------------------------------------------------

max_review_length = 0
i=0
flag=0
for r in df.reviews.tolist():
    i+=1
    if((max_review_length<len(r.split()))):
        flag=i
        max_review_length=max(max_review_length,len(r.split()))
        rr=r

def pad(e, sentence_length=max_review_length):
    # https://stackoverflow.com/questions/35751306/python-how-to-pad-numpy-array-with-zeros
    num_sentences, old_sentence_length, embedding_length = e.shape
    e2 = np.zeros((num_sentences, sentence_length, embedding_length))
    e2[:, :old_sentence_length , :] = e
    return e2

#if want to get embeddings, uncomment this
sys.exit(0)

elmo_model = hub.Module("https://tfhub.dev/google/elmo/2", trainable=True)
sess = tf.InteractiveSession()
sess.run(tf.global_variables_initializer())


asin_length=len(asin_review.keys())

startflag=0

num=startflag
batch_step = 32

for _asin in list(asin_review.keys())[startflag:]:
    num+=1
    all_embeddings=[]
    x=asin_review[_asin]
    
    if(len(x)<=batch_step):
        embeddings = elmo_model(
                x,
                signature="default",
                as_dict=True
            )["elmo"]
        e = sess.run(embeddings)
        e = pad(e)
        all_embeddings.append(e)
        
    if(len(x)>batch_step):
        for i in range(int(len(x)/batch_step)+1):
            print('In num {} : {}/{}'.format(num,i+1,int(len(x)/batch_step)+1))
            left = i*batch_step
            right = (i+1)*batch_step
            this_x = x[left:right]
        
            # due to the +1 in the range(...+1), we can end up
            # with an empty row at the end. just skip it.
            if not this_x:
                continue
        
            embeddings = elmo_model(
                this_x,
                signature="default",
                as_dict=True
            )["elmo"]
            e = sess.run(embeddings)
            e = pad(e)
            all_embeddings.append(e)
            
    #all_embeddings_conct is the final sent embedding
    all_embeddings_conct = np.concatenate(all_embeddings)
    
    filepath='..\\data\\elmo_generate_reviewdata\\'+_asin+'.h5'
    ave_filepath='..\\data\\elmo_generate_reviewdata\\average\\'+_asin+'.h5'
    max_filepath='..\\data\\elmo_generate_reviewdata\\max\\'+_asin+'.h5'
    con_filepath='..\\data\\elmo_generate_reviewdata\\concat\\'+_asin+'.h5'
    #-----calculate max, ave, concantenate for each sent-------------------------
    
    num_of_sent=all_embeddings_conct.shape[0]
    elmo_dimens=1024
    total_ave_embding=np.zeros((num_of_sent,elmo_dimens))
    total_max_embding=np.zeros((num_of_sent,elmo_dimens))
    total_concat_embding=np.zeros((num_of_sent,elmo_dimens*2))
    
    #----------------1.ave-----------------
    j=0
    for each_sent in all_embeddings_conct:
        word_count=len(x[j].split())
        each_ave_embding=np.zeros((elmo_dimens))
        cur_word_ind=0
        for each_word in each_sent:
            if(cur_word_ind>=word_count):
                break
            each_ave_embding=each_ave_embding+each_word
            cur_word_ind+=1
        each_ave_embding=each_ave_embding/word_count
        total_ave_embding[j]=each_ave_embding
        j+=1
    #----------------2.max-----------------
    j=0
    for each_sent in all_embeddings_conct:
        word_count=len(x[j].split())
        each_max_embding=np.zeros((elmo_dimens))
        each_max_embding=each_sent[:word_count,:].max(axis=0)
        total_max_embding[j]=each_max_embding
        j+=1
    
    #----------------3.concantenate-----------------
    total_concat_embding=np.concatenate((total_ave_embding,total_max_embding),axis=1)


#---------------------write to disk------------------------------------------
#-----write ave embedding file------------------
    with h5py.File(ave_filepath, 'w-') as hf:
        hf.create_dataset(_asin,  data=total_ave_embding)
#-----write max embedding file------------------
    with h5py.File(max_filepath, 'w-') as hf:
        hf.create_dataset(_asin,  data=total_max_embding)
#-----write con embedding file------------------
    with h5py.File(con_filepath, 'w-') as hf:
        hf.create_dataset(_asin,  data=total_concat_embding)
      
    print('{}: {}/{} finished!'.format(_asin,num,asin_length))


sess.close()

#
#