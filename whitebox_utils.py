import numpy as np
import json
import pickle
import os
import time
import pprint
import pandas as pd
import keras
import random
from scipy import spatial



def get_prediction_given_tokens(model_type, model, doc, glove_vectors = None, embed_map = None):
    if (model_type == 'LSTM'):
        X_embed = []
        for word in doc:
            if word in embed_map:
                X_embed.append(embed_map['w2i'][word])
            else:
                X_embed.append(random.randint(1,10))

        print(X_embed)
        y = model.predict(X_embed)[0][0]
        return y
        
    elif (model_type == 'LR'):
        X_vector = transform_to_feature_vector(doc, glove_vectors)
        y = model.predict_proba(X_vector)[0][1]
        return y
    
    elif (model_type == 'CNN'):
        print('CNN')




def transform_to_feature_vector(tokens, glove_vectors):
    vectors = []
    for token in tokens:
        if token in glove_vectors:
            vect = glove_vectors[token]
            vectors.append(vect)
        else:
            # sampling from the uniform distribution in [-0.1, 0.1]
            vect = [(random.random()/5)-0.1 for i in range(300)]
            vectors.append(vect)

    means = np.mean(vectors, axis=0)
    return [means] # [ [x11,x12,x13,...]  ]


## SEMANTIC SIMILARITY  -------------------------------------------------------------

def getSemanticSimilarity(X, X_prime, epsilon):
    # Fill after initial testing

    return epsilon + 1





## JACOBIAN MATRIX -------------------------------------------------------------

def get_word_importances_for_whitebox(tokens, glove_vectors):

    ## Transform tokens to the avg feature vector
    vector = transform_to_feature_vector(tokens, glove_vectors)

    ## Load model, get prediction for whole document
    modelFileName = 'Sentiment_Analysis/White_Box/Models/LogisticRegression_RT.pkl'
    with open(modelFileName, 'rb') as fid:
        model = pickle.load(fid)
    pred = model.predict(vector)[0]

    pred_proba = model.predict_proba(vector)[0][1]


    ## Compute importance for each word
    excludes = get_excludes(tokens)         # To see the relative importance of each word, remove that word and predict
    
    JM = {}
    for ex_word, ex_tokens in excludes.items():
        ex_vect = transform_to_feature_vector(ex_tokens, glove_vectors)

        ex_pred_proba = model.predict_proba(ex_vect)[0][1]

        if (pred == 1):
            C = pred_proba - ex_pred_proba
        else:
            C = ex_pred_proba - pred_proba

        JM[ex_word] = C

    ordered_list_by_importance = getImportances(JM)

    return ordered_list_by_importance

def get_excludes(l1):

    res = {}
    for el in l1:
        sub = [x for x in l1 if x != el]
        res[el] = sub
    return res

def getImportances(JM):
    df = pd.DataFrame(JM.items(), columns=['Word', 'C'])

    df = df.sort_values('C', ascending=False)
    return df['Word'].tolist()









## BUG GENERATION  -------------------------------------------------------------

def generateBugs(word, glove_vectors):
    
    bugs = {"insert": word, "delete": word, "swap": word, "sub_C": word, "sub_W": word}

    if (len(word) <= 2):
        return bugs

    bugs["insert"] = bug_insert(word)
    bugs["delete"] = bug_delete(word)
    bugs["swap"] = bug_swap(word)
    bugs["sub_C"] = bug_sub_C(word)
    bugs["sub_W"] = bug_sub_W(word, glove_vectors)

    # pprint.pprint(bugs)

    return bugs

def bug_insert(word):
    if (len(word) >= 6):
        return word
    res = word
    point = random.randint(1, len(word)-1)
    res = res[0:point] + " " + res[point:]
    return res



def bug_delete(word):

    res = word
    point = random.randint(1, len(word)-2)
    res = res[0:point] + res[point+1:]
    # print("hi")
    # print(res[7:])
    return res


def bug_swap(word):
    if (len(word) <= 4):
        return word
    res = word
    points = random.sample(range(1, len(word)-1), 2)
    # print(points)
    a = points[0]
    b = points[1]

    res = list(res)
    w = res[a]
    res[a] = res[b]
    res[b] = w
    res = ''.join(res)
    return res

def bug_sub_C(word):
    res = word
    key_neighbors = get_key_neighbors()
    point = random.randint(0,len(word)-1)

    if word[point] not in key_neighbors:
        return word
    choices = key_neighbors[word[point]]
    subbed_choice = choices[random.randint(0,len(choices)-1)]
    res = list(res)
    res[point] = subbed_choice
    res = ''.join(res)

    return res

def bug_sub_W(word, glove_vectors):
    if word not in glove_vectors:
        return word

    closest_neighbors = find_closest_words(glove_vectors[word], glove_vectors)[1:6]
    
    return random.choice(closest_neighbors)
    # return closest_neighbors # Change later



def get_key_neighbors():
    # By keyboard proximity
    neighbors = {
        "q": "was","w": "qeasd","e": "wrsdf","r": "etdfg","t": "ryfgh","y": "tughj","u": "yihjk","i": "uojkl","o": "ipkl","p": "ol",    
        "a": "qwszx","s": "qweadzx","d": "wersfxc","f": "ertdgcv","g": "rtyfhvb","h": "tyugjbn","j": "yuihknm","k": "uiojlm","l": "opk",      
        "z": "asx","x": "sdzc","c": "dfxv","v": "fgcb","b": "ghvn","n": "hjbm","m": "jkn"
    }

    # By visual proximity
    neighbors['i'] += '1'
    neighbors['l'] += '1'
    neighbors['z'] += '2'
    neighbors['e'] += '3'
    neighbors['a'] += '4'
    neighbors['s'] += '5'
    neighbors['g'] += '6'
    neighbors['b'] += '8'
    neighbors['g'] += '9'
    neighbors['q'] += '9'
    neighbors['o'] += '0'

    return neighbors

def find_closest_words(point, glove_vectors):
    return sorted(glove_vectors.keys(), key=lambda word: spatial.distance.euclidean(glove_vectors[word], point))
