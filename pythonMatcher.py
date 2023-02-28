import logging
import sys
from AlignmentFormat import serialize_mapping_to_tmp_file
from collections import defaultdict
import numpy as np
import random
import json

import os
#from rdflib import Graph, URIRef, RDFS
from bs4 import BeautifulSoup
from owlready2 import onto_path, get_ontology 
import io
from time import sleep
import itertools
from tqdm import tqdm

import urllib.request
from urllib.request import Request, urlopen

import pandas as pd
import torch
from sentence_transformers import SentenceTransformer, util

from langdetect import detect, detect_langs


#Pre-processing the source, target and reference files
# def render_using_label(entity):
#     return entity.label.first() or entity.name

# read ontology with label and name
def read_ontology(file):
    onto = get_ontology(file)
    onto.load()
    base = onto.base_iri

    # Read classes
    entity_list = {}
    label_list = {}
    id_node = 0
    #excl = ['DbXref','Definition','ObsoleteClass','Subset','Synonym','SynonymType']

    for cl in onto.classes(): 
        if cl not in entity_list:
            #if cl.name not in excl:
            entity_list[base+cl.name] = id_node            
            labels = cl.label
            if len(labels)==0:
                label = cl.name
                label = label.lower().replace('_',' ')
                label = label.replace('/',' ')
                label = label.replace("-",' ')
                label = label.replace(" of ",' ')
                label = label.replace(" this ",' ')
                label = label.replace(" the ",' ')
                label = label.replace(" or ",' ')
                label = label.replace(" and ",' ')
                label = label.replace(" that ",' ')
                label = label.replace(" by ",' ')
                label = label.replace(" ",'_')
                label = label.replace("_a_",'_')
                label = label.replace("_an_",'_')
                label = label.replace("_",' ')
                label_list[label] = cl.name 
            else:
                for label in labels:
                    label = label.lower().replace('_',' ')
                    label = label.replace('/',' ')
                    label = label.replace("-",' ')
                    label = label.replace(" of ",' ')
                    label = label.replace(" this ",' ')
                    label = label.replace(" the ",' ')
                    label = label.replace(" or ",' ')
                    label = label.replace(" and ",' ')
                    label = label.replace(" that ",' ')
                    label = label.replace(" by ",' ')
                    label = label.replace(" ",'_')
                    label = label.replace("_a_",'_')
                    label = label.replace("_an_",'_')
                    label = label.replace("_",' ')
                    label_list[label] = cl.name          
        id_node = id_node+1
    excl = ['thing','dbxref','definition','obsoleteclass','subset','synonym','synonymtype']
    for ex in excl:
      try:
        del label_list[ex]
      except KeyError:
        pass 
    
    return entity_list,label_list

def read_food_label(file):
  label_list = {}
  with open(file) as f:
    soup = BeautifulSoup(f,'xml')
    try:
      cells = soup.find_all('owl:Class')
      for cell in tqdm(cells):
        entity = cell.attrs['rdf:about']
        #entity = entity.replace(base,'')      
        if cell.find('skos:hiddenLabel') is not None:
          for labels in cell.findAll('skos:hiddenLabel'):
            label = labels.text
            label_list[label] = entity
    except (KeyError,AttributeError):
      pass
  return label_list

def read_biodiv_label(file):
  label_list = {}
  with open(file) as f:
    soup = BeautifulSoup(f,'xml')
    try:
      cells = soup.find_all('owl:Class')
      for cell in tqdm(cells):
        entity = cell.attrs['rdf:about']
        if cell.find('rdfs:label') is not None:
          for labels in cell.findAll('rdfs:label'):
            label = labels.text
            label = label.lower()
            label = label.replace(" (WRB2006_FR)",'')
            label = label.replace(" (RP2008)",'')
            if label:
              try:
                lang = detect(label)
              except:
                lang = 'Other'
              if lang == 'en':
                label_list[label] = entity
        if cell.find('rdfs:comment') is not None:
          for labels in cell.findAll('rdfs:comment'):
            label = labels.text
            label = label.lower()
            if label:
              try:
                lang = detect(label)
              except:
                lang = 'Other'
              if lang == 'en':
                label_list[label] = entity
    except (KeyError,AttributeError):
      pass
  return label_list

# get syn of entities
def getSyn(file):
    
    entity_list,label_list = read_ontology(file)
    onto = get_ontology(file)
    onto.load()
    base = onto.base_iri
    
    synonym_list = {}
    entity_syn = []

    with open(file) as f:
        soup = BeautifulSoup(f,'xml')
    try:
        cells = soup.find_all('owl:Class')
        for cell in tqdm(cells):
            entity = cell.attrs['rdf:about']
            #entity = entity.replace(base,'')
            if entity in entity_list.keys():        
                if cell.find('oboInOwl:hasRelatedSynonym') is not None:
                    for synonyms in cell.findAll('oboInOwl:hasRelatedSynonym'):
                        synonym = synonyms['rdf:resource']
                        synonym_list[synonym] = entity[17:]
    except (KeyError,AttributeError):
        pass


    with open(file) as f:
        soup = BeautifulSoup(f,'xml')

    try:        
        cells_synonym = soup.find_all('rdf:Description')
        for cell in cells_synonym:
            synonym = cell.attrs['rdf:about']
            if synonym in synonym_list.keys():
                if cell.find('rdfs:label') is not None:
                    synonym_label = cell.find('rdfs:label').string.lower().replace('_',' ')
                    synonym_label = synonym_label.replace('/',' ')
                    synonym_label = synonym_label.replace("-",' ')
                    synonym_label = synonym_label.replace(",",' ')
                    synonym_label = synonym_label.replace(" of ",'')
                    synonym_label = synonym_label.replace(" this ",' ')
                    synonym_label = synonym_label.replace(" the ",' ')
                    synonym_label = synonym_label.replace(" or ",' ')
                    synonym_label = synonym_label.replace(" and ",' ')
                    synonym_label = synonym_label.replace(" that ",' ')
                    synonym_label = synonym_label.replace(" ",'_')
                    synonym_label = synonym_label.replace("_a_",'_')
                    ynonym_label = synonym_label.replace("_an_",'_')
                    synonym_label = synonym_label.replace("_",' ')
                    if synonym_label not in label_list:
                        label_list[synonym_label]=synonym_list.get(synonym)
                        entity_syn.append(synonym_list.get(synonym))
    except (KeyError,AttributeError):
        pass
    
    excl = ['thing','dbxref','definition','obsoleteclass','subset','synonym','synonymtype']
    for ex in excl:
      try:
        del label_list[ex]
      except KeyError:
        pass 
    
    return entity_syn,label_list 

def getSubclass(file):
    subclass = []
    onto = get_ontology(file)
    onto.load()
    
    classes = []
    excl = ['Thing','DbXref','Definition','ObsoleteClass','Subset','Synonym','SynonymType']

    for cl in onto.classes():
        #if cl.name not in excl:
        classes.append(cl)

    classes = list(set(classes))

    for i in range (len(classes)):
        clss = classes[i].name
        for j in range(len(classes[i].is_a)):
            try:
                if classes[i].is_a[j].name not in excl:
                    subclass.append((clss,classes[i].is_a[j].name))
            except AttributeError:
                pass
    return subclass

def getDijclass(file):
    dijclass = []
    onto = get_ontology(file)
    onto.load()
    classes = []
    #excl = ['DbXref','Definition','ObsoleteClass','Subset','Synonym','SynonymType']

    for cl in onto.classes():
        #if cl.name not in excl:
        classes.append(cl.name)

    classes = list(set(classes))

    try:
        for clss in onto.classes():
            for d in clss.disjoints():
              if clss.name != d.entities[0].name:
                dijclass.append((clss.name,d.entities[0].name))
    except AttributeError:
        pass
    return dijclass

def getTriples(file):
    triples = []
    djw_list = {}
    subclass = getSubclass(file)
    dijclass = getDijclass(file)
    classes,labels = read_ontology(file)

    #excl = ['Thing','DbXref','Definition','ObsoleteClass','Subset','Synonym','SynonymType']

    for sub in subclass:
        triples.append([sub[0],'subclass of',sub[1]])

    for dij in dijclass:
        triples.append([dij[0],'disjoint with', dij[1]])

    
    return triples

def alignmentMatch(source_url, target_url):

    urllib.request.urlretrieve(source_url, "source.owl")
    urllib.request.urlretrieve(target_url, "target.owl")
    source_file = "source.owl"
    target_file = "target.owl"

    onto1 = get_ontology(source_file)
    onto1.load()
    base1 = onto1.base_iri

    onto2 = get_ontology(target_file)
    onto2.load()
    base2 = onto2.base_iri

    relation = '='
    alignments = []

    sentences1 = []
    sourceid = []
    sentences2 = []
    targetid = []

    threshold = 0.924

    entity_syn_source,syn_source = getSyn(source_file)
    entity_syn_target,syn_target = getSyn(target_file)

    for key1,val1 in syn_source.items():
        sentences1.append(key1)
        sourceid.append(val1)

    for key2,val2 in syn_target.items():
        sentences2.append(key2)
        targetid.append(val2)

    model = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2')
    embeddings1 = model.encode(sentences1, convert_to_tensor=True)
    embeddings2 = model.encode(sentences2, convert_to_tensor=True)

    cosine_scores = util.cos_sim(embeddings1,embeddings2)

    values,indices = torch.max(cosine_scores,1)

    for i in range(len(sentences1)):
        if cosine_scores[i][indices[i]].item() >= threshold:
            a = base1+sourceid[i]
            b = base2+targetid[indices[i]]
            score = round(cosine_scores[i][indices[i]].item(),3)
            if (a,b,relation,score) not in alignments: 
                alignments.append((a,b,relation,score))

    return alignments

def alignmentMatchFood(source_url, target_url):

    urllib.request.urlretrieve(source_url, "source.xml")
    urllib.request.urlretrieve(target_url, "target.xml")
    source_file = "source.xml"
    target_file = "target.xml"

    relation = '='
    alignments = []

    sentences1 = []
    sourceid = []
    sentences2 = []
    targetid = []

    threshold = 0.924

    source_label_list = read_food_label(source_file)
    target_label_list = read_food_label(target_file)

    for key1,val1 in source_label_list.items():
        sentences1.append(key1)
        sourceid.append(val1)

    for key2,val2 in target_label_list.items():
        sentences2.append(key2)
        targetid.append(val2)

    #print(sentences2)

    model = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2')
    embeddings1 = model.encode(sentences1, convert_to_tensor=True)
    embeddings2 = model.encode(sentences2, convert_to_tensor=True)

    cosine_scores = util.cos_sim(embeddings1,embeddings2)

    values,indices = torch.max(cosine_scores,1)

    for i in range(len(sentences1)):
        if cosine_scores[i][indices[i]].item() >= threshold:
            a = sourceid[i]
            b = targetid[indices[i]]
            score = round(cosine_scores[i][indices[i]].item(),3)
            if (a,b,relation,score) not in alignments: 
                alignments.append((a,b,relation,score))

    return alignments

def alignmentMatchBiodiv(source_url, target_url):

    urllib.request.urlretrieve(source_url, "source.rdf")
    urllib.request.urlretrieve(target_url, "target.rdf")
    source_file = "source.rdf"
    target_file = "target.rdf"

    relation = '='
    alignments = []

    sentences1 = []
    sourceid = []
    sentences2 = []
    targetid = []

    threshold = 0.924

    source_label_list = read_biodiv_label(source_file)
    target_label_list = read_biodiv_label(target_file)

    for key1,val1 in source_label_list.items():
        sentences1.append(key1)
        sourceid.append(val1)

    for key2,val2 in target_label_list.items():
        sentences2.append(key2)
        targetid.append(val2)

    #print(sentences2)

    model = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2')
    embeddings1 = model.encode(sentences1, convert_to_tensor=True)
    embeddings2 = model.encode(sentences2, convert_to_tensor=True)

    cosine_scores = util.cos_sim(embeddings1,embeddings2)

    values,indices = torch.max(cosine_scores,1)

    for i in range(len(sentences1)):
        if cosine_scores[i][indices[i]].item() >= threshold:
            a = sourceid[i]
            b = targetid[indices[i]]
            score = round(cosine_scores[i][indices[i]].item(),3)
            if (a,b,relation,score) not in alignments: 
                alignments.append((a,b,relation,score))

    return alignments

def match(source_url, target_url, input_alignment_url):
    logging.info("Python matcher info: Match " + source_url + " to " + target_url)

    if 'food' in source_url:
        resulting_alignment = alignmentMatchFood(source_url,target_url)
    elif 'biodiv' in source_url:
        resulting_alignment = alignmentMatchBiodiv(source_url,target_url)
    else:
        resulting_alignment = alignmentMatch(source_url, target_url)

    # in case you have the results in a pandas dataframe, make sure you have the columns
    # source (uri), target (uri), relation (usually the string '='), confidence (floating point number)
    # in case relation or confidence is missing use: df["relation"] = '='  and  df["confidence"] = 1.0
    # then select the columns in the right order (like df[['source', 'target', 'relation', 'confidence']])
    # because serialize_mapping_to_tmp_file expects an iterbale of source, target, relation, confidence
    # and then call .itertuples(index=False)
    # example: alignment_file_url = serialize_mapping_to_tmp_file(df[['source', 'target', 'relation', 'confidence']].itertuples(index=False))

    alignment_file_url = serialize_mapping_to_tmp_file(resulting_alignment)
    return alignment_file_url


def main(argv):
    if len(argv) == 2:
        print(match(argv[0], argv[1], None))
    elif len(argv) >= 3:
        if len(argv) > 3:
            logging.error("Too many parameters but we will ignore them.")
        print(match(argv[0], argv[1], argv[2]))
    else:
        logging.error(
            "Too few parameters. Need at least two (source and target URL of ontologies"
        )


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO
    )
    main(sys.argv[1:])
