import re
import os
import json
import time

from flask import Flask, jsonify, render_template
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
	appts = json.loads(resp.text)
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
	web = json.loads(resp.text)
    if resp.status_code == 200:
        return jsonify({ 'appts': appts, 'web': web })
    else:
        return {}
    return "index.html"

@app.route('/people/')
def people_index():
    queries = [ one_query_gen, one_query_spec, desc_query ]
    out = []
    for q in queries:
        data = run_query(q)
        out.append(data)
        time.sleep(5)
    return jsonify(out)

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

def cast_appointment(jdata):
    data = {}
    data['rabid'] = jdata['@id']
    data['name'] = parse_data_property(
        jdata, 'http://www.w3.org/2000/01/rdf-schema#label')
    data['hospital'] = parse_data_property(
        jdata, 'http://vivoweb.org/ontology/core#linkAnchorText')
    data['start'] = parse_data_property(
        jdata, 'http://vivo.brown.edu/ontology/profile#startDate')
    data['end'] = parse_data_property(
        jdata, 'http://vivo.brown.edu/ontology/profile#endDate')
    return data

def parse_appt_data(jdata):
    out = []
    for j in jdata:
        out.append(cast_appointment(j))
    return out

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

@app.route('/people/<shortid>/appointments')
def get_appointments(shortid):
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
        ?appt a bprofile:Appointment .
        ?appt rdfs:label ?a_name .
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

@app.route('/people/<shortid>/credentials')
def get_credentials(shortid):
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
        ?appt a bprofile:Credential .
        ?appt rdfs:label ?a_name .
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

if __name__ == '__main__':
    app.run(host='0.0.0.0')
