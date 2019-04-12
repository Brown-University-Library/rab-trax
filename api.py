import re
import os
import json
import time

from flask import Flask, jsonify
import requests

app = Flask(__name__)
app.config.from_pyfile('config/api.cfg')

os.environ['QUERY'] = app.config['QUERY']
os.environ['UPDATE'] = app.config['UPDATE']
os.environ['USER'] = app.config['USER']
os.environ['PASSW'] = app.config['PASSW']

queryUrl = os.environ['QUERY']
updateUrl = os.environ['UPDATE']
user = os.environ['USER']
passw = os.environ['PASSW']

def parse_JSON_string(stringData):
    jdata = json.loads(stringData)
    print(jdata)
    triples = [ (s, p, o['value'])
                for s, v in jdata.items()
                    for p, z in v.items()
                        for o in z ]
    return triples

many_query = '''
    PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX vivo:     <http://vivoweb.org/ontology/core#>
    CONSTRUCT { ?fac rdfs:label ?label .}
    WHERE
    {
          ?fac a vivo:FacultyMember .
          ?fac rdfs:label ?label .
    }
    LIMIT 10
    '''
one_query_gen = '''
    PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX vivo:     <http://vivoweb.org/ontology/core#>
    CONSTRUCT { <http://vivo.brown.edu/individual/jkauer> ?p ?o .}
    WHERE
    {
          <http://vivo.brown.edu/individual/jkauer> ?p ?o .
    }
    '''
one_query_spec = '''
    PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX vivo:     <http://vivoweb.org/ontology/core#>
    CONSTRUCT { <http://vivo.brown.edu/individual/jkauer> rdfs:label ?label .}
    WHERE
    {
          <http://vivo.brown.edu/individual/jkauer> rdfs:label ?label .
    }
    '''
desc_query = '''
    DESCRIBE <http://vivo.brown.edu/individual/jkauer>
    '''

def run_query(queryText):
    headers = {'Accept': 'application/json', 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': queryText }
    start = time.process_time()
    resp = requests.post(queryUrl, data=data, headers=headers)
    duration = time.process_time() - start
    out = { 'time': duration, 'data': json.loads(resp.text),
        'url': resp.request.url, 'headers': dict(resp.request.headers) }
    return out

@app.route('/')
def index():
    return "RAB TRAX"

@app.route('/people/')
def people_index():
    queries = [ one_query_gen, one_query_spec, desc_query ]
    out = []
    for q in queries:
        data = run_query(q)
        out.append(data)
        time.sleep(5)
    return jsonify(out)

if __name__ == '__main__':
    app.run(host='0.0.0.0')