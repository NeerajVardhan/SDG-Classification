# -*- coding: utf-8 -*-
"""Sariam.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1z_oMPiTB1lUd575uV5ZDKN_rdkUS0i0n

### Libraries
"""

# standard library
from typing import List

# data wrangling
import numpy as np
import pandas as pd

# visualisation
import plotly.express as px
import plotly.io as pio

# nlp
import spacy

# data modelling
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.feature_selection import SelectKBest, chi2, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, f1_score

# utils
from tqdm import tqdm

# local packages
from helpers import plot_confusion_matrix, get_top_features, fix_sdg_name

print('Loaded!')

from google.colab import files
uploaded = files.upload()



# other settings
pio.templates.default = 'plotly_white'

spacy.prefer_gpu()
nlp = spacy.load('en_core_web_sm', disable = ['ner'])

"""## I. Data Preparation

_In this section, we will explore the data and select texts for training._
"""

df_osdg = pd.read_csv('https://zenodo.org/record/5550238/files/osdg-community-dataset-v21-09-30.csv?download=1')
print('Shape:', df_osdg.shape)
display(df_osdg.head())

# calculating cumulative probability over agreement scores
df_lambda = df_osdg['agreement'].value_counts(normalize = True).sort_index().cumsum().to_frame(name = 'p_sum')
df_lambda.reset_index(inplace = True)
df_lambda.rename({'index': 'agreement'}, axis = 1, inplace = True)

print('Shape:', df_lambda.shape)
display(df_lambda.head())

# keeping only the texts whose suggested sdg labels is accepted and the agreement score is at least .6
print('Shape before:', df_osdg.shape)
df_osdg = df_osdg.query('agreement >= .6 and labels_positive > labels_negative').copy()
print('Shape after :', df_osdg.shape)
display(df_osdg.head())

df_lambda = df_osdg.groupby('sdg', as_index = False).agg(count = ('text_id', 'count'))
df_lambda['share'] = df_lambda['count'].divide(df_lambda['count'].sum()).multiply(100)
print('Shape:', df_lambda.shape)
display(df_lambda.head())

def preprocess_spacy(alpha: List[str]) -> List[str]:
   
    docs = list()
    
    for doc in tqdm(nlp.pipe(alpha, batch_size = 128)):
        tokens = list()
        for token in doc:
            if token.pos_ in ['NOUN', 'VERB', 'ADJ']:
                tokens.append(token.lemma_)
        docs.append(' '.join(tokens))
        
    return docs

df_osdg['docs'] = preprocess_spacy(df_osdg['text'].values)
print('Shape:', df_osdg.shape)
display(df_osdg.head())

X_train, X_test, y_train, y_test = train_test_split(
    df_osdg['docs'].values, 
    df_osdg['sdg'].values, 
    test_size = .3,
    random_state = 42
)

print('Shape train:', X_train.shape)
print('Shape test:', X_test.shape)

type(X_train)

#from sklearn.ensemble import AdaBoostClassifier#69

from sklearn.linear_model import SGDClassifier
final = SGDClassifier(loss="hinge", penalty="l2", max_iter=5)
pipe = Pipeline([
    ('vectoriser', TfidfVectorizer(
        ngram_range = (1, 2),
        max_df = 0.75,
        min_df = 2,
        max_features = 100_000
    )),
    ('selector', SelectKBest(f_classif, k = 79_000)),
    ('clf', final)
])

pipe.fit(X_train, y_train)
type(pipe)

y_train

y_hat = pipe.predict(X_test)
plot_confusion_matrix(y_test, y_hat)



from sklearn.svm import SVC
#Degree: 5 =>33
#Degree: 3 =>66
sega = SVC(kernel='poly',degree=1)
pipe = Pipeline([
    ('vectoriser', TfidfVectorizer(ngram_range = (1, 2), max_df = 0.75, min_df = 2, max_features = 100_000)),
    ('selector', SelectKBest(f_classif, k = 1_000)),
    ('clf', sega)
])

pipe.fit(X_train, y_train)
#LEts Try Grid Serch in the  Ski learn
y_hat = pipe.predict(X_test)
plot_confusion_matrix(y_test, y_hat)

from google.colab import drive
drive.mount('/content/drive')

temp = pipe.predict([X_test[2]])

print(temp)

y_hat = pipe.predict(X_test)
plot_confusion_matrix(y_test, y_hat)

from sklearn.model_selection import GridSearchCV
params = {
    'kernel':('linear','poly','rbf','sigmoid'),
    'C':[1,52,10],
    'degree':[3,10],
    'coef0':[0.001,10,0.5],
    'gamma':('auto','scale')
}

SVModel = SVC()
GridS = GridSearchCV(SVModel,params,cv=5)
#GridS.fit(X_train, y_train)

pipe = Pipeline([
    ('vectoriser', TfidfVectorizer(
        ngram_range = (1, 2),
        max_df = 0.75,
        min_df = 2,
        max_features = 100_000
    )),
    ('selector', SelectKBest(f_classif, k = 5_000))
])

X_test

import pickle
pickle_out = open("classifier.pkl","wb")
pickle.dump(pipe, pickle_out)
pickle_out.close()

print(X_test[0])

!pip3 install pdfminer
!pip3 install nltk

import nltk
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
import nltk
import os
import re
import pickle
from datetime import datetime
from sklearn.feature_selection import SelectKBest, chi2, f_classif


def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()

    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    fp.close()
    device.close()
    retstr.close()
    return text


print(datetime.now())
for filename in uploaded.keys():
  text = convert_pdf_to_txt(filename)
  text = re.sub('\s+', ' ', text)
  a = set(nltk.corpus.stopwords.words('english'))
  text1 = nltk.word_tokenize(text.lower())
  stopwords = [x for x in text1 if x not in a]
  text = nltk.word_tokenize(" ".join(map(str, stopwords)))
  finaltext = ''
  for token in text:
    temp = nltk.pos_tag([token])
    if(nltk.pos_tag([token])[0][1] == 'JJ' or nltk.pos_tag([token])[0][1] == 'NN' or nltk.pos_tag([token])[0][1][0] == 'V'):
        finaltext += " "+nltk.pos_tag([token])[0][0]
  # Pass this as an argument when writing the code with frontend INstead of opening it each and evry time
  #prediction = pipe.predict([finaltext])
  #print(prediction)
  print(filename +' rank is ',pipe.predict([finaltext]))

