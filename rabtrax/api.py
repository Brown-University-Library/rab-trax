import re
import csv
import os
import json
import time
import random
from collections import defaultdict

from flask import jsonify, render_template, request
import requests
import SPARQLWrapper

from rabtrax import app, sparqlz

queryUrl = app.config['QUERY']
updateUrl = app.config['UPDATE']
user = app.config['USER']
passw = app.config['PASSW']
dataDir = app.config['DATA']

def parse_data_property(jldObj, prop):
    field = jldObj.get(prop, None)
    if not field:
        return ''
    return field[0]['@value']

def parse_JSON_string(stringData):
    jdata = json.loads(stringData)
    print(jdata)
    triples = [ (s, p, o['value'])
                for s, v in jdata.items()
                    for p, z in v.items()
                        for o in z ]
    return triples

profiling_queries = [
    {
    'name': '10_faculty_with_labels',
    'return': 'set',
    'body': '''
        PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX vivo:     <http://vivoweb.org/ontology/core#>
        CONSTRUCT {{ ?fac rdfs:label ?label .}}
        WHERE
        {{
              ?fac a vivo:FacultyMember .
              ?fac rdfs:label ?label .
        }}
        LIMIT 10
    '''
    },
    {
    'name': 'generic_predicate_object',
    'return': 'graph',
    'body': '''
        PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX vivo:     <http://vivoweb.org/ontology/core#>
        CONSTRUCT {{ <{0}> ?p ?o .}}
        WHERE
        {{
              <{0}> ?p ?o .
        }}
    '''
    },
    {
    'name': 'rdfs_label',
    'return': 'graph',
    'body': '''
        PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX vivo:     <http://vivoweb.org/ontology/core#>
        CONSTRUCT {{ <{0}> rdfs:label ?label .}}
        WHERE
        {{
              <{0}> rdfs:label ?label .
        }}
    '''
    },
    {
    'name': 'describe',
    'return': 'graph',
    'body': 'DESCRIBE <{0}>'
    },
    {
    'name': 'select',
    'return': 'set',
    'body': 'SELECT?p?o WHERE{{<{0}>?p?o.}}'
    },
    {
    'name': 'label_with_optional_overview',
    'return': 'graph',
    'body': '''
        PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX vivo:     <http://vivoweb.org/ontology/core#>
        CONSTRUCT {{
            <{0}> rdfs:label ?label .
            <{0}> vivo:overview ?ovr .
        }}
        WHERE
        {{
              <{0}> rdfs:label ?label .
              OPTIONAL {{ <{0}> vivo:overview ?ovr .}}
        }}
    '''
    },
    {
    'name': 'optional_profile_data_properties',
    'return': 'graph',
    'body': '''
        PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX vivo:     <http://vivoweb.org/ontology/core#>
        PREFIX blocal:   <http://vivo.brown.edu/ontology/vivo-brown/>
        CONSTRUCT {{
            <{0}> blocal:fullName ?full .
            <{0}> blocal:alphaName ?alpha .
            <{0}> blocal:affiliations ?affiliations .
            <{0}> blocal:awardsAndHonors ?awards .
            <{0}> blocal:fundedResarch ?funded .
            <{0}> blocal:researchStatement ?statement .
            <{0}> blocal:scholarlyWork ?scholarly .
            <{0}> vivo:overview ?over .
            <{0}> vivo:researchOverview ?res_over .
            <{0}> vivo:teachingOverview ?teach_over .
        }}
        WHERE
        {{
            <{0}> blocal:fullName ?full .
            <{0}> blocal:alphaName ?alpha .
            OPTIONAL {{ <{0}> blocal:affiliations ?affiliations . }}
            OPTIONAL {{ <{0}> blocal:awardsAndHonors ?awards . }}
            OPTIONAL {{ <{0}> blocal:fundedResarch ?funded . }}
            OPTIONAL {{ <{0}> blocal:researchStatement ?statement . }}
            OPTIONAL {{ <{0}> blocal:scholarlyWork ?scholarly . }}
            OPTIONAL {{ <{0}> vivo:overview ?over . }}
            OPTIONAL {{ <{0}> vivo:researchOverview ?res_over . }}
            OPTIONAL {{ <{0}> vivo:teachingOverview ?teach_over . }}
        }}
    '''
    },
    {
    'name': 'optional_profile_data_properties_with_type',
    'return': 'graph',
    'body': '''
        PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX vivo:     <http://vivoweb.org/ontology/core#>
        PREFIX blocal:   <http://vivo.brown.edu/ontology/vivo-brown/>
        CONSTRUCT {{
            <{0}> blocal:fullName ?full .
            <{0}> blocal:alphaName ?alpha .
            <{0}> blocal:affiliations ?affiliations .
            <{0}> blocal:awardsAndHonors ?awards .
            <{0}> blocal:fundedResarch ?funded .
            <{0}> blocal:researchStatement ?statement .
            <{0}> blocal:scholarlyWork ?scholarly .
            <{0}> vivo:overview ?over .
            <{0}> vivo:researchOverview ?res_over .
            <{0}> vivo:teachingOverview ?teach_over .
        }}
        WHERE
        {{
            <{0}> rdf:type vivo:FacultyMember .
            <{0}> blocal:fullName ?full .
            <{0}> blocal:alphaName ?alpha .
            OPTIONAL {{ <{0}> blocal:affiliations ?affiliations . }}
            OPTIONAL {{ <{0}> blocal:awardsAndHonors ?awards . }}
            OPTIONAL {{ <{0}> blocal:fundedResarch ?funded . }}
            OPTIONAL {{ <{0}> blocal:researchStatement ?statement . }}
            OPTIONAL {{ <{0}> blocal:scholarlyWork ?scholarly . }}
            OPTIONAL {{ <{0}> vivo:overview ?over . }}
            OPTIONAL {{ <{0}> vivo:researchOverview ?res_over . }}
            OPTIONAL {{ <{0}> vivo:teachingOverview ?teach_over . }}
        }}
    '''
    },
    {
    'name': 'describe_links_with_filtering',
    'return': 'graph',
    'body': '''
        PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX owl:      <http://www.w3.org/2002/07/owl#>
        DESCRIBE ?uri
        WHERE {{
            <{0}> ?p ?uri .
            ?p rdf:type owl:ObjectProperty .
        }}
    '''
    },
    {
    'name': 'describe_links',
    'return': 'graph',
    'body': '''
        DESCRIBE ?uri
        WHERE {{
            <{0}> ?p ?uri .
        }}
    '''
    },
    {
    'name': 'describe_links_rev',
    'return': 'graph',
    'body': '''
        DESCRIBE ?uri
        WHERE {{
            ?uri ?p <{0}>.
        }}
    '''
    },
    {
    'name': 'select_links_label',
    'return': 'set',
    'body': '''
        PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?p ?uri ?label
        WHERE {{
            <{0}> ?p ?uri .
            ?uri rdfs:label ?label .
        }}
    '''
    }
]

def parse_set_json(jdata):
    rows = []
    for j in jdata['results']['bindings']:
        rows.append({ k: v['value'] for k, v in j.items() })
    return len(rows)

def parse_graph_json(jdata):
    rows = []
    for j in jdata:
        uri = j['@id']
        data = { k: len(v) if isinstance(v, list) else v for k,v in j.items() }
        rows.append({ uri: data })
    return rows

def run_query(query, auth, accept='json'):
    uri = 'http://vivo.brown.edu/individual/{}'.format(auth)
    if query['return'] == 'set':
        if accept == 'xml':
            mime = 'application/sparql-results+xml'
        else:
            mime = 'application/sparql-results+json'
    else:
        if accept == 'xml':
            mime = 'application/rdf+xml'
        else:
            mime = 'application/json'
    headers = {'Accept': mime, 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': query['body'].format(uri) }
    start = time.process_time()
    resp = requests.post(queryUrl, data=data, headers=headers)
    duration = time.process_time() - start
    if accept == 'json':
        data = json.loads(resp.text)
    else:
        data = resp.text
    out = {}
    if query['return'] == 'set':
        if accept == 'xml':
            out['data'] = data
        else:
            out['data'] = parse_set_json(data)
    else:
        if accept == 'xml':
            out['data'] = data
        else:
            out['data'] = parse_graph_json(data)
    out['size'] = len(resp.text)
    out['elapsed_time'] = duration
    return out

@app.route('/profiling/run', methods=["POST"])
def run_queries_for_profiling():
    data = request.get_json()
    queries = [ q for q in profiling_queries
        if q['name'] in data['queries'] ]
    batch = int(data['trials'])
    with open(os.path.join(dataDir, 'recent_shortids.csv'), 'r') as f:
        rdr = csv.reader(f)
        next(rdr) #skip header
        auth_ids = [ row[0] for row in rdr ]
    out = []
    random.shuffle(auth_ids)
    for e, q in enumerate(queries):
        print('query: {}'.format(q['name']))
        stats = { 'details': {},
            'avg_time': 0, 'avg_size': 0 }
        auths = auth_ids[batch*e:batch*e+batch]
        for auth in auths:
            print('....{}'.format(auth))
            stats['details'][auth] = run_query(q, auth, accept=data['accept'])
            stats['avg_time'] += stats['details'][auth]['elapsed_time']
            stats['avg_size'] += stats['details'][auth]['size']
            time.sleep(1)
        stats['query'] = q['name']
        stats['avg_time'] = format(stats['avg_time']/batch, '.8g')
        stats['avg_size'] = format(stats['avg_size']/batch, '.8g')
        stats['details'] = json.dumps(
            stats['details'], indent=4, sort_keys=True)
        out.append( stats )
    out = sorted(out, key=lambda stat: stat['avg_time'])
    return jsonify( out )

@app.route('/profiling')
def query_profiling():
    queries = [
        {
        'name': q['name'],
        'body':q['body'].format('http://example.com') }
            for q in profiling_queries ]
    return render_template('query_profiling.html', queries=queries)

@app.route('/')
def index():
    query = '''	
	PREFIX blocal:   <http://vivo.brown.edu/ontology/vivo-brown/>
	PREFIX bprofile: <http://vivo.brown.edu/ontology/profile#>
	SELECT ?fac ?shortid (count(?appt) as ?c)
	WHERE
	{
	?fac bprofile:hasAppointment ?appt .
	?fac blocal:shortId ?shortid
	}
	GROUP BY ?fac ?shortid
	ORDER BY DESC(?c)
	LIMIT 10
    '''
    headers = {'Accept': 'text/csv', 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': query }
    resp = requests.post(queryUrl, data=data, headers=headers)
    rdr = csv.reader(resp.text)
    appts = [ row for row in csv.reader(resp.text.split('\n')) ][1:-1]
    query = '''
    PREFIX blocal:   <http://vivo.brown.edu/ontology/vivo-brown/>
    SELECT ?fac ?shortid (count(?web) as ?c)
    WHERE
    {
	?fac blocal:drrbWebPage ?web .
        ?fac blocal:shortId ?shortid
    }
    GROUP BY ?fac ?shortid
    ORDER BY DESC(?c)
	LIMIT 10
    '''
    headers = {'Accept': 'text/csv', 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': query }
    resp = requests.post(queryUrl, data=data, headers=headers)
    web = [ row for row in csv.reader(resp.text.split('\n')) ][1:-1]
    if resp.status_code == 200:
        return render_template('index.html', web=web, appts=appts)
    else:
        return {}

@app.route('/people/<shortid>')
def get_person(shortid):
    query = '''
    PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX vivo:     <http://vivoweb.org/ontology/core#>
    PREFIX blocal:   <http://vivo.brown.edu/ontology/vivo-brown/>
    CONSTRUCT {{
        <http://vivo.brown.edu/individual/{0}> blocal:fullName ?full .
        <http://vivo.brown.edu/individual/{0}> blocal:alphaName ?alpha .
        <http://vivo.brown.edu/individual/{0}> blocal:affiliations ?affiliations .
        <http://vivo.brown.edu/individual/{0}> blocal:awardsAndHonors ?awards .
        <http://vivo.brown.edu/individual/{0}> blocal:fundedResarch ?funded .
        <http://vivo.brown.edu/individual/{0}> blocal:researchStatement ?statement .
        <http://vivo.brown.edu/individual/{0}> blocal:scholarlyWork ?scholarly .
        <http://vivo.brown.edu/individual/{0}> vivo:overview ?over .
        <http://vivo.brown.edu/individual/{0}> vivo:researchOverview ?res_over .
        <http://vivo.brown.edu/individual/{0}> vivo:teachingOverview ?teach_over .
    }}
    WHERE
    {{
        <http://vivo.brown.edu/individual/{0}> blocal:fullName ?full .
        <http://vivo.brown.edu/individual/{0}> blocal:alphaName ?alpha .
        OPTIONAL {{ <http://vivo.brown.edu/individual/{0}> blocal:affiliations ?affiliations . }}
        OPTIONAL {{ <http://vivo.brown.edu/individual/{0}> blocal:awardsAndHonors ?awards . }}
        OPTIONAL {{ <http://vivo.brown.edu/individual/{0}> blocal:fundedResarch ?funded . }}
        OPTIONAL {{ <http://vivo.brown.edu/individual/{0}> blocal:researchStatement ?statement . }}
        OPTIONAL {{ <http://vivo.brown.edu/individual/{0}> blocal:scholarlyWork ?scholarly . }}
        OPTIONAL {{ <http://vivo.brown.edu/individual/{0}> vivo:overview ?over . }}
        OPTIONAL {{ <http://vivo.brown.edu/individual/{0}> vivo:researchOverview ?res_over . }}
        OPTIONAL {{ <http://vivo.brown.edu/individual/{0}> vivo:teachingOverview ?teach_over . }}
    }}
    '''.format(shortid)
    headers = {'Accept': 'application/json', 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': query }
    resp = requests.post(queryUrl, data=data, headers=headers)
    if resp.status_code == 200:
        return jsonify(json.loads(resp.text))
    else:
        return {}

@app.route('/people/<shortid>/overview')
def get_overview(shortid):
    query = '''
    PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX vivo:     <http://vivoweb.org/ontology/core#>
    PREFIX blocal:   <http://vivo.brown.edu/ontology/vivo-brown/>
    CONSTRUCT {{
        <http://vivo.brown.edu/individual/{0}> vivo:overview ?over .
    }}
    WHERE
    {{
        <http://vivo.brown.edu/individual/{0}> vivo:overview ?over .
    }}
    '''.format(shortid)
    headers = {'Accept': 'application/json', 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': query }
    resp = requests.post(queryUrl, data=data, headers=headers)
    if resp.status_code == 200:
        data = json.loads(resp.text)
        return jsonify( parse_data_property(
            data[0], 'http://vivoweb.org/ontology/core#overview'))
    else:
        return {}


@app.route('/people/<shortid>/describe')
def describe_person(shortid):
    query = 'DESCRIBE <http://vivo.brown.edu/individual/{}>'.format(shortid)
    headers = {'Accept': 'application/json', 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': query }
    resp = requests.post(queryUrl, data=data, headers=headers)
    if resp.status_code == 200:
        return jsonify(json.loads(resp.text))
    else:
        return {}

@app.route('/people/<shortid>/ras')
def get_research_areas(shortid):
    query = '''
    PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX vivo:     <http://vivoweb.org/ontology/core#>
    CONSTRUCT {{ ?ra rdfs:label ?name . }}
    WHERE
    {{
        <http://vivo.brown.edu/individual/{}> vivo:hasResearchArea ?ra .
        ?ra rdfs:label ?name .
    }}
    '''.format(shortid)
    headers = {'Accept': 'application/json', 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': query }
    resp = requests.post(queryUrl, data=data, headers=headers)
    if resp.status_code == 200:
        return jsonify(json.loads(resp.text))
    else:
        return {}

@app.route('/people/<shortid>/appt_combined')
def get_combined_appointment(shortid):
    data = {}
    start = time.process_time()
    data['data'] = get_appointment_data(shortid)
    data['objs'] = get_appoinment_objects(shortid)
    duration = time.process_time() - start
    data['time'] = duration
    return jsonify(data)

@app.route('/people/<shortid>/appt_data')
def get_appointment_data(shortid):
    query = '''
    PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX vivo:     <http://vivoweb.org/ontology/core#>
    PREFIX bprofile: <http://vivo.brown.edu/ontology/profile#>
    CONSTRUCT {{
        ?appt rdfs:label ?a_name .
        ?appt bprofile:startDate ?start .
        ?appt bprofile:endDate ?end .
        ?appt bprofile:department ?dept .
        ?appt bprofile:number ?number .
        ?appt bprofile:country ?country .
        ?appt bprofile:city ?city .
        ?appt bprofile:state ?state .
    }}
    WHERE
    {{
        <http://vivo.brown.edu/individual/{}> bprofile:hasAppointment ?appt .
        ?appt rdfs:label ?a_name .
        OPTIONAL {{ ?appt bprofile:startDate ?start . }}
        OPTIONAL {{ ?appt bprofile:endDate ?end . }}
        OPTIONAL {{ ?appt bprofile:department ?dept . }}
        OPTIONAL {{ ?appt bprofile:number ?number . }}
        OPTIONAL {{ ?appt bprofile:country ?country . }}
        OPTIONAL {{ ?appt bprofile:city ?city . }}
        OPTIONAL {{ ?appt bprofile:state ?state  . }}
    }}
    '''.format(shortid)
    headers = {'Accept': 'application/json', 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': query }
    resp = requests.post(queryUrl, data=data, headers=headers)
    if resp.status_code == 200:
        return json.loads(resp.text)
    else:
        return {}

@app.route('/people/<shortid>/appt_objs')
def get_appoinment_objects(shortid):
    query = '''
    PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX vivo:     <http://vivoweb.org/ontology/core#>
    PREFIX bprofile: <http://vivo.brown.edu/ontology/profile#>
    CONSTRUCT {{
        ?obj rdfs:label ?name .
    }}
    WHERE
    {{
        {{
            <http://vivo.brown.edu/individual/{0}> bprofile:hasAppointment ?appt .
            ?appt bprofile:hasHospital ?obj .
            ?obj rdfs:label ?name .
        }} UNION {{
            <http://vivo.brown.edu/individual/{0}> bprofile:hasOrganization ?appt .
            ?appt bprofile:hasOrganization ?obj .
            ?obj rdfs:label ?name .
        }} UNION {{
            <http://vivo.brown.edu/individual/{0}> bprofile:hasAppointment ?appt .
            ?appt bprofile:hasSpecialty ?obj .
            ?obj rdfs:label ?name .
        }}
    }}
    '''.format(shortid)
    headers = {'Accept': 'application/json', 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': query }
    resp = requests.post(queryUrl, data=data, headers=headers)
    if resp.status_code == 200:
        return json.loads(resp.text)
    else:
        return {}

def cast_appointment(jdata, labelMap):
    data = {}
    data['rabid'] = jdata['@id']
    data['title'] = parse_data_property(
        jdata, 'http://www.w3.org/2000/01/rdf-schema#label')
    if jdata.get('http://vivo.brown.edu/ontology/profile#hasHospital'):
        h_obj = jdata['http://vivo.brown.edu/ontology/profile#hasHospital'][0]
        data['org'] = {}
        data['org']['rabid'] = h_obj['@id']
        data['org']['name'] = labelMap[h_obj['@id']]
    data['start'] = parse_data_property(
        jdata, 'http://vivo.brown.edu/ontology/profile#startDate')
    data['end'] = parse_data_property(
        jdata, 'http://vivo.brown.edu/ontology/profile#endDate')
    return data

def isAppointment(jdata):
    appt_types = { "http://vivo.brown.edu/ontology/profile#HospitalAppointment" }
    return set(jdata.get('@type', [None])) & appt_types

def parse_appt_data(jdata):
    skip = { 'http://vivo.brown.edu/ontology/profile#HospitalAppointment',
        'http://www.w3.org/2002/07/owl#Thing'}
    flt = [ d for d in jdata if d['@id'] not in skip ]
    label_map = {
        d['@id'] : d['http://www.w3.org/2000/01/rdf-schema#label'][0]['@value']
            for d in flt }
    out = []
    for j in flt:
        if isAppointment(j):
            out.append(cast_appointment(j, label_map))
    return out

@app.route('/people/<shortid>/appointments')
def get_appointments(shortid):
    query = '''
    PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX vivo:     <http://vivoweb.org/ontology/core#>
    PREFIX bprofile: <http://vivo.brown.edu/ontology/profile#>
    CONSTRUCT {{
        ?appt rdfs:label ?a_name .
        ?appt rdf:type ?type .
        ?appt bprofile:startDate ?start .
        ?appt bprofile:endDate ?end .
        ?appt bprofile:department ?dept .
        ?appt bprofile:number ?number .
        ?appt bprofile:country ?country .
        ?appt bprofile:city ?city .
        ?appt bprofile:state ?state .
        ?appt bprofile:hasOrganization ?org.
        ?org rdfs:label ?o_name .
        ?appt bprofile:hasHospital ?hosp .
        ?hosp rdfs:label ?h_name .
        ?appt bprofile:hasSpecialty ?spec. 
        ?spec rdfs:label ?s_name .
    }}
    WHERE
    {{
        <http://vivo.brown.edu/individual/{}> bprofile:hasAppointment ?appt .
        ?appt rdfs:label ?a_name .
        ?appt rdf:type ?type .
        OPTIONAL {{ ?appt bprofile:startDate ?start . }}
        OPTIONAL {{ ?appt bprofile:endDate ?end . }}
        OPTIONAL {{ ?appt bprofile:department ?dept . }}
        OPTIONAL {{ ?appt bprofile:number ?number . }}
        OPTIONAL {{ ?appt bprofile:country ?country . }}
        OPTIONAL {{ ?appt bprofile:city ?city . }}
        OPTIONAL {{ ?appt bprofile:state ?state  . }}
        OPTIONAL {{ ?appt bprofile:hasHospital ?hosp .
            ?hosp rdfs:label ?h_name . }}
        OPTIONAL {{ ?appt bprofile:hasOrganization ?org. 
            ?org rdfs:label ?o_name . }}
        OPTIONAL {{ ?appt bprofile:hasSpecialty ?spec. 
            ?spec rdfs:label ?s_name . }}
    }}
    '''.format(shortid)
    headers = {'Accept': 'application/json', 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': query }
    resp = requests.post(queryUrl, data=data, headers=headers)
    if resp.status_code == 200:
        data = json.loads(resp.text)
        return jsonify(parse_appt_data(data))
    else:
        return {}

@app.route('/people/<shortid>/credentials')
def get_credentials(shortid):
    query = '''
    PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX vivo:     <http://vivoweb.org/ontology/core#>
    PREFIX bprofile: <http://vivo.brown.edu/ontology/profile#>
    CONSTRUCT {{
        ?appt rdfs:label ?a_name .
        ?appt rdf:type ?type .
        ?appt bprofile:startDate ?start .
        ?appt bprofile:endDate ?end .
        ?appt bprofile:department ?dept .
        ?appt bprofile:number ?number .
        ?appt bprofile:country ?country .
        ?appt bprofile:city ?city .
        ?appt bprofile:state ?state .
        ?appt bprofile:hasOrganization ?org.
        ?org rdfs:label ?o_name .
        ?appt bprofile:hasHospital ?hosp .
        ?hosp rdfs:label ?h_name .
        ?appt bprofile:hasSpecialty ?spec. 
        ?spec rdfs:label ?s_name .
    }}
    WHERE
    {{
        <http://vivo.brown.edu/individual/{}> bprofile:hasAppointment ?appt .
        ?appt rdfs:label ?a_name .
        ?appt rdf:type ?type .
        OPTIONAL {{ ?appt bprofile:startDate ?start . }}
        OPTIONAL {{ ?appt bprofile:endDate ?end . }}
        OPTIONAL {{ ?appt bprofile:department ?dept . }}
        OPTIONAL {{ ?appt bprofile:number ?number . }}
        OPTIONAL {{ ?appt bprofile:country ?country . }}
        OPTIONAL {{ ?appt bprofile:city ?city . }}
        OPTIONAL {{ ?appt bprofile:state ?state  . }}
        OPTIONAL {{ ?appt bprofile:hasHospital ?hosp .
            ?hosp rdfs:label ?h_name . }}
        OPTIONAL {{ ?appt bprofile:hasOrganization ?org. 
            ?org rdfs:label ?o_name . }}
        OPTIONAL {{ ?appt bprofile:hasSpecialty ?spec. 
            ?spec rdfs:label ?s_name . }}
    }}
    '''.format(shortid)
    headers = {'Accept': 'application/json', 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': query }
    resp = requests.post(queryUrl, data=data, headers=headers)
    if resp.status_code == 200:
        return jsonify(json.loads(resp.text))
    else:
        return {}

def cast_weblink(jdata):
    data = {}
    data['rabid'] = jdata['@id']
    data['link_text'] = parse_data_property(
        jdata, 'http://vivoweb.org/ontology/core#linkAnchorText')
    data['url'] = parse_data_property(
        jdata, 'http://vivoweb.org/ontology/core#linkURI')
    data['rank'] = parse_data_property(
        jdata, 'http://vivoweb.org/ontology/core#rank')
    return data

def parse_weblink_data(jdata):
    out = []
    for j in jdata:
        out.append(cast_weblink(j))
    return out

@app.route('/people/<shortid>/weblinks')
def get_weblinks(shortid):
    query = '''
    PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX vivo:     <http://vivoweb.org/ontology/core#>
    PREFIX blocal:   <http://vivo.brown.edu/ontology/vivo-brown/>
    CONSTRUCT {{
        ?web rdfs:label ?label .
        ?web vivo:linkAnchorText ?text .
        ?web vivo:rank ?rank .
        ?web vivo:linkURI ?uri .
    }}
    WHERE
    {{
        <http://vivo.brown.edu/individual/{}> blocal:drrbWebPage ?web .
        ?web rdfs:label ?label .
        ?web vivo:linkAnchorText ?text .
        ?web vivo:rank ?rank .
        ?web vivo:linkURI ?uri .
    }}
    '''.format(shortid)
    headers = {'Accept': 'application/json', 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': query }
    resp = requests.post(queryUrl, data=data, headers=headers)
    if resp.status_code == 200:
        parsed = parse_weblink_data(json.loads(resp.text))
        return jsonify(parsed)
    else:
        return {}

@app.route('/profile/<shortid>')
def profile_editor(shortid):
    return render_template('profile.html', shortid=shortid)

def rest_get_overview(shortid):
    query = '''
    PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX vivo:     <http://vivoweb.org/ontology/core#>
    PREFIX blocal:   <http://vivo.brown.edu/ontology/vivo-brown/>
    CONSTRUCT {{
        <http://vivo.brown.edu/individual/{0}> vivo:overview ?over .
    }}
    WHERE
    {{
        <http://vivo.brown.edu/individual/{0}> vivo:overview ?over .
    }}
    '''.format(shortid)
    headers = {'Accept': 'application/json', 'charset':'utf-8'}
    data = { 'email': user, 'password': passw, 'query': query }
    resp = requests.post(queryUrl, data=data, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        if data:
            parsed = parse_data_property(
                data[0], 'http://vivoweb.org/ontology/core#overview')
            return {'overview': parsed }
        else:
            return {'overview': '' }
    else:
        return { 'error': resp.text }

def clean_literal(literal): 
    literal = literal.strip() 
    if literal.startswith('"') and literal.endswith('"'): 
        return literal[1:-1] 
    return literal

def prep_string_input(input):
    return input.replace('"', r'\"')

# https://www.w3.org/TR/sparql11-query/#grammarEscapes
def rest_update_overview(shortId, add, rmv):
    query = '''
    PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX vivo:     <http://vivoweb.org/ontology/core#>
    PREFIX blocal:   <http://vivo.brown.edu/ontology/vivo-brown/>
    '''
    del_cmd = "DELETEDATA{{GRAPH{0}{{<http://vivo.brown.edu/individual/{1}>vivo:overview'''{2}'''.}}}}"
    ins_cmd = "INSERTDATA{{GRAPH{0}{{<http://vivo.brown.edu/individual/{1}>vivo:overview'''{2}'''.}}}}"
    graph = '<http://vitro.mannlib.cornell.edu/default/vitro-kb-2>'
    if rmv:
        query += del_cmd.format(graph, shortId, rmv)
    if add and rmv:
        query += ';'
    if add:
        query += ins_cmd.format(graph, shortId, add)
    headers = {}
    data = { 'email': user, 'password': passw, 'update': query }
    resp = requests.post(updateUrl, data=data, headers=headers)
    return resp

@app.route('/profile/<shortId>/overview',
    methods=['GET', 'POST', 'PUT', 'DELETE'])
def rest_overview(shortId):
    if request.method == 'GET':
        data = rest_get_overview(shortId)
        return jsonify(data)
    if request.method == 'POST':
        data = request.get_json()
        resp = rest_update_overview(shortId, data['overview'], None)
        if resp.status_code == 200:
            return jsonify(data)
        else:
            return jsonify({ 'error': resp.text })
    if request.method == 'PUT':
        data = request.get_json()
        existing = rest_get_overview(shortId)
        resp = rest_update_overview(shortId, data['overview'], existing['overview'])
        if resp.status_code == 200:
            return jsonify(data)
        else:
            return jsonify({ 'error': resp.text })
    if request.method == 'DELETE':
        existing = rest_get_overview(shortId)
        resp = rest_update_overview(shortId, None, existing['overview'])
        return jsonify({ 'message': resp.text })

def shortIdToUri(shortId):
    return 'http://vivo.brown.edu/individual/{0}'.format(shortId)

@app.route('/data/<shortid>')
def get_person_data(shortid):
    full = request.args.get('full')
    start = time.process_time()
    data = sparqlz.get(shortIdToUri(shortid), full)
    duration = time.process_time() - start
    return jsonify({ 'data': data, 'duration': duration })


def get_faculty(shortid):
    fac = Faculty.query.filter_by(shortid=shortid).first()
    if fac:
        return jsonify(fac.to_json())
    return jsonify({})

def query_faculty(shortId):
    remote = SPARQLWrapper.SPARQLWrapper(queryUrl, updateUrl)
    remote.addParameter('email', user)
    remote.addParameter('password', passw)
    remote.setMethod(SPARQLWrapper.POST)
    remote.setQuery(
        "DESCRIBE ?uri WHERE {{ VALUES ?uri {{ <{0}> }} }}".format(
            shortIdToUri(shortId)) )
    results = remote.queryAndConvert()
    out = defaultdict(list)
    for r in results.triples((None,None,None)):
        out[r[1].toPython()].append(r[2].toPython())
    return out

property_map = {
    'overview' : 'http://vivoweb.org/ontology/core#overview',
    'research_overview' : 'http://vivoweb.org/ontology/core#researchOverview',
    'research_statement' : 'http://vivo.brown.edu/ontology/vivo-brown/researchStatement',
    'funded_research' : 'http://vivo.brown.edu/ontology/vivo-brown/fundedResearch',
    'affiliations': 'http://vivo.brown.edu/ontology/vivo-brown/affiliations',
    'awards_honors': 'http://vivo.brown.edu/ontology/vivo-brown/awardsAndHonors',
    'teaching_overview': 'http://vivoweb.org/ontology/core#teachingOverview',

    'teacherFor': 'http://vivo.brown.edu/ontology/vivo-brown/teacherFor',
    'citation#contributorTo': 'http://vivo.brown.edu/ontology/citation#contributorTo',
    'fundedResearch': 'http://vivo.brown.edu/ontology/vivo-brown/fundedResearch',
    'core#educationalTraining': 'http://vivoweb.org/ontology/core#educationalTraining',
    'hasGeographicResearchArea': 'http://vivo.brown.edu/ontology/vivo-brown/hasGeographicResearchArea',
    'core#researchOverview': 'http://vivoweb.org/ontology/core#researchOverview',
    'lastName': 'http://xmlns.com/foaf/0.1/lastName',
    'core#hasCollaborator': 'http://vivoweb.org/ontology/core#hasCollaborator',
    'core#hasResearchArea': 'http://vivoweb.org/ontology/core#hasResearchArea',
    'public#mainImage': 'http://vitro.mannlib.cornell.edu/ns/vitro/public#mainImage',
    '22-rdf-syntax-ns#type': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
    '0.7#mostSpecificType': 'http://vitro.mannlib.cornell.edu/ns/vitro/0.7#mostSpecificType',
    'pubmedLastName': 'http://vivo.brown.edu/ontology/vivo-brown/pubmedLastName',
    'hasAffiliation': 'http://vivo.brown.edu/ontology/vivo-brown/hasAffiliation',
    'researchStatement': 'http://vivo.brown.edu/ontology/vivo-brown/researchStatement',
    'profileUpdated': 'http://vivo.brown.edu/ontology/vivo-brown/profileUpdated',
    'core#primaryEmail': 'http://vivoweb.org/ontology/core#primaryEmail',
    'cv': 'http://vivo.brown.edu/ontology/vivo-brown/cv',
    'fisCreated': 'http://vivo.brown.edu/ontology/vivo-brown/fisCreated',
    'shortId': 'http://vivo.brown.edu/ontology/vivo-brown/shortId',
    'profile#hasTraining': 'http://vivo.brown.edu/ontology/profile#hasTraining',
    'fisUpdated': 'http://vivo.brown.edu/ontology/vivo-brown/fisUpdated',
    'core#personInPosition': 'http://vivoweb.org/ontology/core#personInPosition',
    'core#preferredTitle': 'http://vivoweb.org/ontology/core#preferredTitle',
    'rdf-schema#label': 'http://www.w3.org/2000/01/rdf-schema#label',
    'alphaName': 'http://vivo.brown.edu/ontology/vivo-brown/alphaName',
    'previousImage': 'http://vivo.brown.edu/ontology/vivo-brown/previousImage',
    'fullName': 'http://vivo.brown.edu/ontology/vivo-brown/fullName',
    'core#overview': 'http://vivoweb.org/ontology/core#overview',
    'core#teachingOverview': 'http://vivoweb.org/ontology/core#teachingOverview',
    'pubmedFirstName': 'http://vivo.brown.edu/ontology/vivo-brown/pubmedFirstName',
    'drrbWebPage': 'http://vivo.brown.edu/ontology/vivo-brown/drrbWebPage',
    'primaryOrgLabel': 'http://vivo.brown.edu/ontology/vivo-brown/primaryOrgLabel',
    'firstName': 'http://xmlns.com/foaf/0.1/firstName',
    'scholarlyWork': 'http://vivo.brown.edu/ontology/vivo-brown/scholarlyWork'
}

@app.route('/<shortId>/faculty/edit/overview/overview/update')
def profile_overview(shortId):
    data = query_faculty(shortId)
    return jsonify({'overview': data[ property_map['overview'] ]})


@app.route('/<shortId>/faculty/edit/research/overview/update')
def profile_research_overview(shortId):
    data = query_faculty(shortId)
    return jsonify({'research_overview': data[ property_map['research_overview'] ]})


@app.route('/<shortId>/faculty/edit/research/statement/update')
def profile_research_statement(shortId):
    data = query_faculty(shortId)
    return jsonify({'research_statement': data[ property_map['research_statement'] ]})


@app.route('/<shortId>/faculty/edit/research/funded/update')
def profile_funded_research(shortId):
    data = query_faculty(shortId)
    return jsonify({'funded_research': data[ property_map['funded_research'] ]})


@app.route('/<shortId>/faculty/edit/background/honors/update')
def profile_awards_honors(shortId):
    data = query_faculty(shortId)
    return jsonify({'awards_honors': data[ property_map['awards_honors'] ]})


@app.route('/<shortId>/faculty/edit/affiliations/affiliations/update')
def profile_affiliations(shortId):
    data = query_faculty(shortId)
    return jsonify({'affiliations': data[ property_map['affiliations'] ]})


@app.route('/<shortId>/faculty/edit/teaching/overview/update')
def profile_teaching_overview(shortId):
    data = query_faculty(shortId)
    return jsonify({'teaching_overview': data[ property_map['teaching_overview'] ]})