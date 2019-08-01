import re
import csv
import os
import json
import time
import random
import uuid
from collections import defaultdict, namedtuple
from datetime import datetime as dt

from flask import jsonify, render_template, request
import requests
import SPARQLWrapper

from rabtrax import app, sparqlz, models

queryUrl = app.config['QUERY']
updateUrl = app.config['UPDATE']
user = app.config['USER']
passw = app.config['PASSW']
dataDir = app.config['DATA']


property_map = {
    'overview' : 'http://vivoweb.org/ontology/core#overview',
    'research_overview' : 'http://vivoweb.org/ontology/core#researchOverview',
    'research_statement' : 'http://vivo.brown.edu/ontology/vivo-brown/researchStatement',
    'funded_research' : 'http://vivo.brown.edu/ontology/vivo-brown/fundedResearch',
    'affiliations' : 'http://vivo.brown.edu/ontology/vivo-brown/affiliations',
    'awards_honors' : 'http://vivo.brown.edu/ontology/vivo-brown/awardsAndHonors',
    'teaching_overview' : 'http://vivoweb.org/ontology/core#teachingOverview',
    'label' : 'http://www.w3.org/2000/01/rdf-schema#label',
    'research_areas' : 'http://vivoweb.org/ontology/core#hasResearchArea',
    'web_links' : 'http://vivo.brown.edu/ontology/vivo-brown/drrbWebPage',
    'link_text' : 'http://vivoweb.org/ontology/core#linkAnchorText',
    'link_url' : 'http://vivoweb.org/ontology/core#linkURI',
    'rank' : 'http://vivoweb.org/ontology/core#rank',
    'collaborators' : 'http://vivoweb.org/ontology/core#hasCollaborator',
    'trainings' : 'http://vivo.brown.edu/ontology/profile#hasTraining',
    'credentials': 'http://vivo.brown.edu/ontology/profile#hasCredential',
    'appointments': 'http://vivo.brown.edu/ontology/profile#hasAppointment',
    'start_date' : 'http://vivo.brown.edu/ontology/profile#startDate',
    'end_date' : 'http://vivo.brown.edu/ontology/profile#endDate',
    'credential_number' : 'http://vivo.brown.edu/ontology/profile#credentialNumber',
    'credential_grantor' : 'http://vivo.brown.edu/ontology/profile#credentialGrantedBy',
    'specialty' : 'http://vivo.brown.edu/ontology/profile#hasSpecialty',
    'department' : 'http://vivo.brown.edu/ontology/profile#department',
    'hospital' : 'http://vivo.brown.edu/ontology/profile#hasHospital',
    'organization' : 'http://vivo.brown.edu/ontology/profile#hasOrganization',
    'city' : 'http://vivo.brown.edu/ontology/profile#city',
    'state' : 'http://vivo.brown.edu/ontology/profile#state',
    'country' : 'http://vivo.brown.edu/ontology/profile#country',

    'teacherFor': 'http://vivo.brown.edu/ontology/vivo-brown/teacherFor',
    'citation#contributorTo': 'http://vivo.brown.edu/ontology/citation#contributorTo',
    'core#educationalTraining': 'http://vivoweb.org/ontology/core#educationalTraining',
    'hasGeographicResearchArea': 'http://vivo.brown.edu/ontology/vivo-brown/hasGeographicResearchArea',
    'lastName': 'http://xmlns.com/foaf/0.1/lastName',
    'public#mainImage': 'http://vitro.mannlib.cornell.edu/ns/vitro/public#mainImage',
    '22-rdf-syntax-ns#type': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
    '0.7#mostSpecificType': 'http://vitro.mannlib.cornell.edu/ns/vitro/0.7#mostSpecificType',
    'pubmedLastName': 'http://vivo.brown.edu/ontology/vivo-brown/pubmedLastName',
    'hasAffiliation': 'http://vivo.brown.edu/ontology/vivo-brown/hasAffiliation',
    'profileUpdated': 'http://vivo.brown.edu/ontology/vivo-brown/profileUpdated',
    'core#primaryEmail': 'http://vivoweb.org/ontology/core#primaryEmail',
    'cv': 'http://vivo.brown.edu/ontology/vivo-brown/cv',
    'fisCreated': 'http://vivo.brown.edu/ontology/vivo-brown/fisCreated',
    'shortId': 'http://vivo.brown.edu/ontology/vivo-brown/shortId',
    'fisUpdated': 'http://vivo.brown.edu/ontology/vivo-brown/fisUpdated',
    'core#personInPosition': 'http://vivoweb.org/ontology/core#personInPosition',
    'core#preferredTitle': 'http://vivoweb.org/ontology/core#preferredTitle',
    'rdf-schema#label': 'http://www.w3.org/2000/01/rdf-schema#label',
    'alphaName': 'http://vivo.brown.edu/ontology/vivo-brown/alphaName',
    'previousImage': 'http://vivo.brown.edu/ontology/vivo-brown/previousImage',
    'fullName': 'http://vivo.brown.edu/ontology/vivo-brown/fullName',
    'pubmedFirstName': 'http://vivo.brown.edu/ontology/vivo-brown/pubmedFirstName',
    'primaryOrgLabel': 'http://vivo.brown.edu/ontology/vivo-brown/primaryOrgLabel',
    'firstName': 'http://xmlns.com/foaf/0.1/firstName',
    'scholarlyWork': 'http://vivo.brown.edu/ontology/vivo-brown/scholarlyWork'
}


def write_update_query(obj):
    delete_template = u"DELETEDATA{{GRAPH{0}{{{1}}}}}"
    insert_template = u"INSERTDATA{{GRAPH{0}{{{1}}}}}"
    pbody = ""
    delete_triples = ""
    for triple in obj.remove:
        delete_triples += write_statement(triple)
    insert_triples = ""
    for triple in obj.add:
        insert_triples += write_statement(triple)
    if delete_triples:
        pbody += delete_template.format(obj.graph, delete_triples)
    if delete_triples and insert_triples:
        pbody += ";"
    if insert_triples:
        pbody += insert_template.format(obj.graph, insert_triples)
    return pbody

DataDiff = namedtuple('DataDiff', 'add remove graph')
def update_models(models):
    add = set()
    rmv = set()
    graphs = set()
    for m in models:
        graphs.add(m.graph)
        add |= m.add
        rmv |= m.remove
    if len(graphs) != 1 :
        raise Exception('Cannot update by named graph')
    if len(add | rmv) == 0:
        return '200 No update'
    query = write_update_query( DataDiff(add=(add - rmv),
        remove=(rmv - add), graph=graphs.pop() ) )
    remote = SPARQLWrapper.SPARQLWrapper(updateUrl)
    remote.addParameter('email', user)
    remote.addParameter('password', passw)
    remote.setMethod(SPARQLWrapper.POST)
    remote.setQuery(query)
    results = remote.queryAndConvert().decode('utf-8')
    return results


def shortIdToUri(shortId):
    return 'http://vivo.brown.edu/individual/{0}'.format(shortId)


def write_statement(triple):
    return "{0}{1}{2}.".format(*triple)


def query_credential(shortId):
    uri = shortIdToUri(shortId)
    cred_prop = property_map['credentials']
    spec_prop = property_map['specialty']
    grant_prop = property_map['credential_grantor']
    label_prop = property_map['label']
    remote = SPARQLWrapper.SPARQLWrapper(queryUrl, updateUrl)
    remote.addParameter('email', user)
    remote.addParameter('password', passw)
    remote.setMethod(SPARQLWrapper.POST)
    remote.setQuery("""
        DESCRIBE ?uri ?x1 ?x2 ?x3
        WHERE {{
          ?uri <{1}> ?x1 .
          OPTIONAL {{?x1 <{2}> ?x2 .}}
          OPTIONAL {{?x1 <{3}> ?x3 .}}
          values ?uri {{ <{0}> }}
        }}""".format(uri, cred_prop, spec_prop, grant_prop) )
    results = remote.queryAndConvert()
    resources = defaultdict(lambda: defaultdict(list))
    for r in results.triples((None,None,None)):
        resources[r[0].toPython()][r[1].toPython()].append(r[2].toPython())
    fac = resources[uri]
    credentials = [ (cred, resources[cred]) for cred in
        fac.get(cred_prop, []) ]
    out = []
    for rabid, data in credentials:
        data['rabid'] = rabid
        if data.get(spec_prop):
            data[spec_prop] = [
                { 'rabid': spec, 'label': resources[spec][label_prop] }
                    for spec in data[spec_prop] ]
        if data.get(grant_prop):
            data[grant_prop] = [
                { 'rabid': grant, 'label': resources[grant][label_prop] }
                    for grant in data[grant_prop] ]
        out.append(data)
    return out


def query_appointment(shortId):
    uri = shortIdToUri(shortId)
    appt_prop = property_map['appointments']
    hosp_prop = property_map['hospital']
    org_prop = property_map['organization']
    label_prop = property_map['label']
    remote = SPARQLWrapper.SPARQLWrapper(queryUrl, updateUrl)
    remote.addParameter('email', user)
    remote.addParameter('password', passw)
    remote.setMethod(SPARQLWrapper.POST)
    remote.setQuery("""
        DESCRIBE ?uri ?x1 ?x2 ?x3
        WHERE {{
          ?uri <{1}> ?x1 .
          OPTIONAL {{?x1 <{2}> ?x2 .}}
          OPTIONAL {{?x1 <{3}> ?x3 .}}
          values ?uri {{ <{0}> }}
        }}""".format(uri, appt_prop, hosp_prop, org_prop) )
    results = remote.queryAndConvert()
    resources = defaultdict(lambda: defaultdict(list))
    for r in results.triples((None,None,None)):
        resources[r[0].toPython()][r[1].toPython()].append(r[2].toPython())
    fac = resources[uri]
    appointments = [ (appt, resources[appt]) for appt in
        fac.get(appt_prop, []) ]
    out = []
    for rabid, data in appointments:
        data['rabid'] = rabid
        if data.get(hosp_prop):
            data[hosp_prop] = [
                { 'rabid': hosp, 'label': resources[hosp][label_prop] }
                    for hosp in data[hosp_prop] ]
        if data.get(org_prop):
            data[org_prop] = [
                { 'rabid': org, 'label': resources[org][label_prop] }
                    for org in data[org_prop] ]
        out.append(data)
    return out


def query_training(shortId):
    uri = shortIdToUri(shortId)
    train_prop = property_map['trainings']
    spec_prop = property_map['specialty']
    hosp_prop = property_map['hospital']
    org_prop = property_map['organization']
    label_prop = property_map['label']
    remote = SPARQLWrapper.SPARQLWrapper(queryUrl, updateUrl)
    remote.addParameter('email', user)
    remote.addParameter('password', passw)
    remote.setMethod(SPARQLWrapper.POST)
    remote.setQuery("""
        DESCRIBE ?uri ?x1 ?x2 ?x3 ?x4
        WHERE {{
          ?uri <{1}> ?x1 .
          OPTIONAL {{?x1 <{2}> ?x2 .}}
          OPTIONAL {{?x1 <{3}> ?x3 .}}
          OPTIONAL {{?x1 <{4}> ?x4 .}}
          values ?uri {{ <{0}> }}
        }}""".format(uri, train_prop, spec_prop, hosp_prop, org_prop) )
    results = remote.queryAndConvert()
    resources = defaultdict(lambda: defaultdict(list))
    for r in results.triples((None,None,None)):
        resources[r[0].toPython()][r[1].toPython()].append(r[2].toPython())
    fac = resources[uri]
    trainings = [ (train, resources[train]) for train in
        fac.get(train_prop, []) ]
    out = []
    for rabid, data in trainings:
        data['rabid'] = rabid
        if data.get(spec_prop):
            data[spec_prop] = [
                { 'rabid': spec, 'label': resources[spec][label_prop] }
                    for spec in data[spec_prop] ]
        if data.get(hosp_prop):
            data[hosp_prop] = [
                { 'rabid': hosp, 'label': resources[hosp][label_prop] }
                    for hosp in data[hosp_prop] ]
        if data.get(org_prop):
            data[org_prop] = [
                { 'rabid': org, 'label': resources[org][label_prop] }
                    for org in data[org_prop] ]
        out.append(data)
    return out


def query_faculty_association(shortId, assocProp):
    remote = SPARQLWrapper.SPARQLWrapper(queryUrl, updateUrl)
    remote.addParameter('email', user)
    remote.addParameter('password', passw)
    remote.setMethod(SPARQLWrapper.POST)
    remote.setQuery(
        """
        DESCRIBE ?assoc
        WHERE {{ ?uri <{1}> ?assoc.
        VALUES ?uri {{ <{0}> }}
        }}""".format(
            shortIdToUri(shortId), assocProp) )
    results = remote.queryAndConvert()
    out = defaultdict(lambda: defaultdict(list))
    for r in results.triples((None,None,None)):
        out[r[0]][r[1].toPython()].append(r[2].toPython())
    return out


def mint_uri():
    qtext = "ASK WHERE {{ {{ <{0}> ?p ?o. }} UNION {{ ?s ?p2 <{0}> }} }}"
    remote = SPARQLWrapper.SPARQLWrapper(queryUrl, updateUrl)
    remote.setReturnFormat('json')
    remote.addParameter('email', user)
    remote.addParameter('password', passw)
    remote.setMethod(SPARQLWrapper.POST)
    new_uri = False
    tries = 0
    while not new_uri and tries < 50:
        uri = 'http://vivo.brown.edu/individual/n{}'.format(
            uuid.uuid4().hex)
        remote.setQuery( qtext.format(uri) )
        resp = remote.queryAndConvert()
        if not resp['boolean']:
            new_uri = uri
        else:
            tries += 1
    return new_uri


def make_filter(var, prop, ovar, val):
    out = {}
    if prop:
        out['filter'] = '{0}{1}{2}. '.format(var,prop,ovar)
    if val:
        out['values'] = 'VALUES {0} {{ {1} }} '.format(ovar,val)
    return out


def query_research_areas(uris=None, faculty=None, name=None):
    filters = []
    if faculty:
        filters.append(
            make_filter('?ra',
                '<http://vivoweb.org/ontology/core#researchAreaOf>',
                '?fac',
                '<{}>'.format(faculty) ) )
    if name:
        filters.append(
            make_filter('?ra',
                '<http://www.w3.org/2000/01/rdf-schema#label>',
                '?name',
                '{}'.format(json.dumps(name)) ) )
    if uris:
        filters.append(
            make_filter(None,None,'?ra',''.join( ['<{}>'.format(u) for u in uris ]) ) )
    query = """
        PREFIX blocal: <http://vivo.brown.edu/ontology/vivo-brown/>
        DESCRIBE ?ra
        WHERE {{ ?ra a blocal:ResearchArea . {0} {1} }}
        """.format(''.join([ f['filter'] for f in filters if f.get('filter') ]),
         ''.join([ f['values'] for f in filters if f.get('values') ]) )
    remote = SPARQLWrapper.SPARQLWrapper(queryUrl, updateUrl)
    remote.addParameter('email', user)
    remote.addParameter('password', passw)
    remote.setMethod(SPARQLWrapper.POST)
    remote.setQuery( query )
    results = remote.queryAndConvert()
    resources = defaultdict(lambda: defaultdict(list))
    for r in results.triples((None,None,None)):
        resources[r[0].toPython()][r[1].toPython()].append(r[2].toPython())
    out = []
    for r in resources:
        res = models.ResearchArea(uri=r)
        res.load(resources[r])
        out.append(res)
    return out


def query_web_links(uris=None, faculty=None, link_text=None,
    link_address=None, rank=None):
    filters = []
    if faculty:
        filters.append(
            make_filter('?link',
                '<http://vivo.brown.edu/ontology/vivo-brown/drrbWebPageOf>',
                '?fac',
                '<{}>'.format(faculty) ) )
    if link_text:
        filters.append(
            make_filter('?link',
                '<http://vivoweb.org/ontology/core#linkAnchorText>',
                '?link_text',
                '{}'.format(json.dumps(link_text)) ) )
    if link_address:
        filters.append(
            make_filter('?link',
                '<http://vivoweb.org/ontology/core#linkURI>',
                '?link_address',
                '{}'.format(json.dumps(link_address)) ) )
    if rank:
        filters.append(
            make_filter('?link',
                '<http://vivoweb.org/ontology/core#rank>',
                '?rank',
                '{}'.format(json.dumps(rank)) ) )
    if uris:
        filters.append(
            make_filter(None,None,'?link',''.join( ['<{}>'.format(u) for u in uris ]) ) )
    query = """
        PREFIX core: <http://vivoweb.org/ontology/core#>
        DESCRIBE ?link
        WHERE {{ ?link a core:URLLink . {0} {1} }}
        """.format(''.join([ f['filter'] for f in filters if f.get('filter') ]),
         ''.join([ f['values'] for f in filters if f.get('values') ]) )
    remote = SPARQLWrapper.SPARQLWrapper(queryUrl, updateUrl)
    remote.addParameter('email', user)
    remote.addParameter('password', passw)
    remote.setMethod(SPARQLWrapper.POST)
    remote.setQuery( query )
    results = remote.queryAndConvert()
    resources = defaultdict(lambda: defaultdict(list))
    for r in results.triples((None,None,None)):
        resources[r[0].toPython()][r[1].toPython()].append(r[2].toPython())
    out = []
    for r in resources:
        res = models.WebLink(uri=r)
        res.load(resources[r])
        out.append(res)
    return out


def query_faculty(shortId):
    uri = shortIdToUri(shortId)
    remote = SPARQLWrapper.SPARQLWrapper(queryUrl, updateUrl)
    remote.addParameter('email', user)
    remote.addParameter('password', passw)
    remote.setMethod(SPARQLWrapper.POST)
    remote.setQuery(
        "DESCRIBE ?uri WHERE {{ VALUES ?uri {{ <{0}> }} }}".format(uri) )
    results = remote.queryAndConvert()
    out = defaultdict(list)
    for r in results.triples((None,None,None)):
        out[r[1].toPython()].append(r[2].toPython())
    profile = models.FacultyProfile(uri)
    profile.load(out)
    return profile


def update_profile(profile):
    if len(profile.add | profile.remove) == 0:
        return '200 No update'
    remote = SPARQLWrapper.SPARQLWrapper(updateUrl)
    remote.addParameter('email', user)
    remote.addParameter('password', passw)
    remote.setMethod(SPARQLWrapper.POST)
    remote.setQuery(write_update_query(profile))
    results = remote.queryAndConvert().decode('utf-8')
    return results


@app.route('/profile/<shortId>/faculty/edit/overview/overview',
    methods=['GET'])
def get_overview(shortId):
    profile = query_faculty(shortId)
    return jsonify({'overview': profile.overview[0] })


@app.route('/profile/<shortId>/faculty/edit/overview/overview/update',
    methods=['POST'])
def update_overview(shortId):
    data = request.get_json(force=True)
    profile = query_faculty(shortId)
    profile.update('overview', [ data['overview'] ] )
    results = update_profile(profile)
    if '200' in results:
        return jsonify({'overview': profile.overview[0] })
    else:
        return jsonify({'error': 'I\'m working on it!'})


@app.route('/profile/<shortId>/faculty/edit/overview/research-areas',
    methods=['GET'])
def get_research_areas(shortId):
    uri = shortIdToUri(shortId)
    data = query_research_areas(faculty=uri)
    return jsonify( { 'research_areas': [
        { 'rabid': ra.uri, 'name': ra.name[0] } for ra in data ] } )


@app.route('/profile/<shortId>/faculty/edit/overview/research-areas/add',
    methods=['POST'])
def add_research_areas(shortId):
    data = request.get_json(force=True)
    profile = query_faculty(shortId)
    ras = query_research_areas(uris=profile.research_areas, faculty=profile.uri)
    for ra in ras:
        if data['name'] == ra.name[0]:
            return jsonify({ 'rabid': ra.uri })
    existing = query_research_areas(name=data['name'])
    if not existing:
        uri = mint_uri()
        if not uri:
            raise Exception('Failure to create new URI')
        ra = models.ResearchArea(uri)
        ra.update('name', [ data['name'] ])
    else:
        ra = existing[0]
    ras_uris = { u for u in profile.research_areas }
    ras_uris.add(ra.uri)
    profile.update('research_areas', list(ras_uris))
    fac_uris = { u for u in ra.faculty }
    fac_uris.add(profile.uri)
    ra.update('faculty', list(fac_uris))
    results = update_models([ra, profile])
    if '200' in results:
        return jsonify({'rabid': ra.uri })
    else:
        return jsonify({'error': 'I\'m working on it!'})


@app.route('/profile/<shortId>/faculty/edit/overview/research-areas/delete',
    methods=['POST'])
def remove_research_areas(shortId):
    data = request.get_json(force=True)
    uri = data['rabid']
    profile = query_faculty(shortId)
    if uri not in profile.research_areas:
        return jsonify({})
    ras = [ r for r in profile.research_areas if r != uri ]
    profile.update('research_areas', ras)
    ra = query_research_areas(uris=[ uri ])[0]
    faculty = [ f for f in ra.faculty if f != profile.uri ]
    ra.update('faculty',faculty)
    results = update_models([ra, profile])
    if '200' in results:
        return jsonify({'deleted': data['rabid'] })
    else:
        return jsonify({'error': 'I\'m working on it!'})


@app.route('/profile/<shortId>/faculty/edit/overview/ontheweb')
def get_web_links(shortId):
    uri = shortIdToUri(shortId)
    data = query_web_links(faculty=uri)
    return jsonify(
        { 'web_links': [ {
            'rabid': link.uri,
            'text': link.link_text[0],
            'url': link.link_address[0],
            'rank': link.rank[0] } for link in data ] })


@app.route('/profile/<shortId>/faculty/edit/overview/ontheweb/add',
    methods=['POST'])
def add_weblink(shortId):
    data = request.get_json(force=True)
    profile = query_faculty(shortId)
    links = query_web_links(uris=profile.web_links, faculty=profile.uri)
    for link in links:
        if data['url'] == link.link_address[0] and data['text'] == link.link_text[0]:
            return jsonify({ 'rabid': link.uri })
    uri = mint_uri()
    if not uri:
        raise Exception('Failure to create new URI')
    link = models.WebLink(uri)
    link.update('link_text', [ data['text'] ])
    link.update('link_address', [ data['url'] ])
    link.update('rank', [ data['rank'] ])
    link.update('faculty', [ profile.uri ] )
    link_uris = { u for u in profile.web_links }
    link_uris.add(link.uri)
    profile.update('web_links', list(link_uris))
    results = update_models([link, profile])
    if '200' in results:
        return jsonify({'rabid': link.uri })
    else:
        return jsonify({'error': 'I\'m working on it!'})


@app.route('/profile/<shortId>/faculty/edit/overview/ontheweb/delete',
    methods=['POST'])
def remove_weblink(shortId):
    data = request.get_json(force=True)
    uri = data['rabid']
    profile = query_faculty(shortId)
    if uri not in profile.web_links:
        return jsonify({})
    links = [ l for l in profile.web_links if l != uri ]
    profile.update('web_links', links)
    link = query_web_links(uris=[ uri ])[0]
    link.update('link_text', [])
    link.update('link_address', [])
    link.update('rank', [])
    link.update('faculty', [])
    link.update('rdfType', [])
    results = update_models([link, profile])
    if '200' in results:
        return jsonify({'deleted': data['rabid'] })
    else:
        return jsonify({'error': 'I\'m working on it!'})


@app.route('/profile/<shortId>/faculty/edit/overview/ontheweb/update',
    methods=['POST'])
def update_weblink(shortId):
    data = request.get_json(force=True)
    profile = query_faculty(shortId)
    if data['rabid'] not in profile.web_links:
        return jsonify({})
    link = query_web_links(uris=[ data['rabid'] ])[0]
    link.update('link_text', [ data['text'] ])
    link.update('link_address', [ data['url'] ])
    link.update('rank', [ data['rank'] ])
    profile.update('last_updated', [ dt.now() ])
    results = update_models([link,profile])
    if '200' in results:
        return jsonify( { 'rabid': link.uri, 'text': link.link_text[0],
            'url': link.link_address[0], 'rank': link.rank[0] } )
    else:
        return jsonify({'error': 'I\'m working on it!'})


@app.route('/profile/<shortId>/faculty/edit/background/training/update')
def profile_training(shortId):
    training = property_map['trainings']
    props = {
        'rabid' : 'rabid',
        property_map['specialty']: 'specialty',
        property_map['hospital']: 'hospital',
        property_map['organization']: 'organization',
        property_map['city']: 'city',
        property_map['state']: 'state',
        property_map['country']: 'country',
        property_map['start_date']: 'start',
        property_map['end_date']: 'end',
        property_map['label']: 'training'
    }
    data = query_training(shortId)
    out = []
    for d in data:
        flt = { props[p]: d[p] for p in props if p in d }
        out.append(flt)
    return jsonify(out)


@app.route('/profile/<shortId>/faculty/edit/background/honors',
    methods=['GET'])
def get_awards_honors(shortId):
    profile = query_faculty(shortId)
    return jsonify({'awards_honors': profile.awards_honors[0] })


@app.route('/profile/<shortId>/faculty/edit/background/honors/update',
    methods=['POST'])
def update_awards_honors(shortId):
    data = request.get_json(force=True)
    profile = query_faculty(shortId)
    profile.update('awards_honors', [ data['awards_honors'] ] )
    results = update_profile(profile)
    if '200' in results:
        return jsonify({'awards_honors': profile.awards_honors[0] })
    else:
        return jsonify({'error': 'I\'m working on it!'})


@app.route('/profile/<shortId>/faculty/edit/teaching/overview',
    methods=['GET'])
def get_teaching_overview(shortId):
    profile = query_faculty(shortId)
    return jsonify({'teaching_overview': profile.teaching_overview[0] })


@app.route('/profile/<shortId>/faculty/edit/teaching/overview/update',
    methods=['POST'])
def update_teaching_overview(shortId):
    data = request.get_json(force=True)
    profile = query_faculty(shortId)
    profile.update('teaching_overview', [ data['teaching_overview'] ] )
    results = update_profile(profile)
    if '200' in results:
        return jsonify({'teaching_overview': profile.teaching_overview[0] })
    else:
        return jsonify({'error': 'I\'m working on it!'})


@app.route('/profile/<shortId>/faculty/edit/research/overview',
    methods=['GET'])
def get_research_overview(shortId):
    profile = query_faculty(shortId)
    return jsonify({'research_overview': profile.research_overview[0] })


@app.route('/profile/<shortId>/faculty/edit/research/overview/update',
    methods=['POST'])
def update_research_overview(shortId):
    data = request.get_json(force=True)
    profile = query_faculty(shortId)
    profile.update('research_overview', [ data['research_overview'] ] )
    results = update_profile(profile)
    if '200' in results:
        return jsonify({'research_overview': profile.research_overview[0] })
    else:
        return jsonify({'error': 'I\'m working on it!'})


@app.route('/profile/<shortId>/faculty/edit/research/statement',
    methods=['GET'])
def get_research_statement(shortId):
    profile = query_faculty(shortId)
    return jsonify({'research_statement': profile.research_statement[0] })


@app.route('/profile/<shortId>/faculty/edit/research/statement/update',
    methods=['POST'])
def update_research_statement(shortId):
    data = request.get_json(force=True)
    profile = query_faculty(shortId)
    profile.update('research_statement', [ data['research_statement'] ] )
    results = update_profile(profile)
    if '200' in results:
        return jsonify({'research_statement': profile.research_statement[0] })
    else:
        return jsonify({'error': 'I\'m working on it!'})


@app.route('/profile/<shortId>/faculty/edit/research/funded',
    methods=['GET'])
def get_funded_research(shortId):
    profile = query_faculty(shortId)
    return jsonify({'funded_research': profile.funded_research[0] })


@app.route('/profile/<shortId>/faculty/edit/research/funded/update',
    methods=['POST'])
def update_funded_research(shortId):
    data = request.get_json(force=True)
    profile = query_faculty(shortId)
    profile.update('funded_research', [ data['funded_research'] ] )
    results = update_profile(profile)
    if '200' in results:
        return jsonify({'funded_research': profile.funded_research[0] })
    else:
        return jsonify({'error': 'I\'m working on it!'})


@app.route('/profile/<shortId>/faculty/edit/research/scholarly',
    methods=['GET'])
def get_scholarly_work(shortId):
    profile = query_faculty(shortId)
    return jsonify({'scholarly_work': profile.scholarly_work[0] })


@app.route('/profile/<shortId>/faculty/edit/research/scholarly/update',
    methods=['POST'])
def update_scholarly_work(shortId):
    data = request.get_json(force=True)
    profile = query_faculty(shortId)
    profile.update('scholarly_work', [ data['scholarly_work'] ] )
    results = update_profile(profile)
    if '200' in results:
        return jsonify({'scholarly_work': profile.scholarly_work[0] })
    else:
        return jsonify({'error': 'I\'m working on it!'})


@app.route('/profile/<shortId>/faculty/edit/affiliations/affiliations',
    methods=['GET'])
def get_affiliations(shortId):
    profile = query_faculty(shortId)
    return jsonify({'affiliations': profile.affiliations[0] })


@app.route('/profile/<shortId>/faculty/edit/affiliations/affiliations/update',
    methods=['POST'])
def update_affiliations(shortId):
    data = request.get_json(force=True)
    profile = query_faculty(shortId)
    profile.update('affiliations', [ data['affiliations'] ] )
    results = update_profile(profile)
    if '200' in results:
        return jsonify({'affiliations': profile.affiliations[0] })
    else:
        return jsonify({'error': 'I\'m working on it!'})


@app.route('/profile/<shortId>/faculty/edit/affiliations/collaborators/update')
def profile_collaborators(shortId):
    data = query_faculty_association(
        shortId, property_map['collaborators'])
    label = property_map['label']
    return jsonify(
        { 'collaborators':
            [ { 'rabid': k,
                'label': data[k].get(label,[''])[0] } for k in data ] })


@app.route('/profile/<shortId>/faculty/edit/affiliations/credential/update')
def profile_credentials(shortId):
    credential = property_map['credentials']
    props = {
        'rabid' : 'rabid',
        property_map['specialty']: 'specialty',
        property_map['credential_grantor']: 'granted_by',
        property_map['credential_number']: 'number',
        property_map['start_date']: 'start',
        property_map['end_date']: 'end',
        property_map['label']: 'credential'
    }
    data = query_credential(shortId)
    out = []
    for d in data:
        flt = { props[p]: d[p] for p in props if p in d }
        out.append(flt)
    return jsonify(out)


@app.route('/profile/<shortId>/faculty/edit/affiliations/appointment/update')
def profile_appointments(shortId):
    appointment = property_map['appointments']
    props = {
        'rabid' : 'rabid',
        property_map['hospital']: 'hospital',
        property_map['organization']: 'organization',
        property_map['department']: 'department',
        property_map['start_date']: 'start',
        property_map['end_date']: 'end',
        property_map['label']: 'appointment'
    }
    data = query_appointment(shortId)
    out = []
    for d in data:
        flt = { props[p]: d[p] for p in props if p in d }
        out.append(flt)
    return jsonify(out)