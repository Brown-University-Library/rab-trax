from rabtrax import app

import requests
import lxml.etree as ET

from collections import defaultdict
import json

queryUrl = app.config['QUERY']
updateUrl = app.config['UPDATE']
user = app.config['USER']
passw = app.config['PASSW']

RDF = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'

def prepJsonData(jsonData, uri):
    data = {}
    links = []
    for jd in jsonData:
        if jd['@id'] == uri:
            data = jd
        elif 'vivo.brown.edu/individual' in jd['@id']:
            links.append(jd['@id'])
    data['links'] = links
    return data

def elementToDict(elem):
    d = defaultdict(list)
    for child in elem.getchildren():
        tag = "".join(child.tag[1:].split('}'))
        res = child.get(RDF + 'resource')
        val = child.text
        if res:
            d[tag].append(res)
        elif val:
            d[tag].append(val.strip())
        else:
            raise Exception(tag)
    return dict(d)

def xmlToGraph(xmlString):
    graph = {}
    tree = ET.fromstring(xmlString)
    for elem in tree.findall(RDF + 'Description'):
        uri = elem.get(RDF + 'about')
        if not uri:
            raise Exception(elem)
        graph[uri] = elementToDict(elem)
    return graph

def describeLinks(uri):
    query = 'DESCRIBE?link WHERE{{<{0}>?p?link}}'.format(uri)
    headers = {'Accept': 'application/rdf+xml', 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': query }
    resp = requests.post(queryUrl, data=data, headers=headers)
    if resp.status_code == 200:
        return resp.text
    else:
        return ''

def describe(uri):
    query = 'DESCRIBE<{0}>'.format(uri)
    headers = {'Accept': 'application/rdf+xml', 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': query }
    resp = requests.post(queryUrl, data=data, headers=headers)
    if resp.status_code == 200:
        return resp.text
    else:
        return ''

def get(uri, get_links=None):
    res = xmlToGraph(describe(uri))
    if get_links:
        links = xmlToGraph(describeLinks(uri))
    else:
        links = {}
    return { 'resource': res, 'links': links }