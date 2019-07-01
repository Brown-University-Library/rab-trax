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
    'training' : 'http://vivo.brown.edu/ontology/profile#hasTraining',
    'start_date' : 'http://vivo.brown.edu/ontology/profile#startDate',
    'end_date' : 'http://vivo.brown.edu/ontology/profile#endDate',
    'credentials': 'http://vivo.brown.edu/ontology/profile#hasCredential',
    'credential_number' : 'http://vivo.brown.edu/ontology/profile#credentialNumber',
    'credential_grantor' : 'http://vivo.brown.edu/ontology/profile#credentialGrantedBy',
    'specialty' : 'http://vivo.brown.edu/ontology/profile#hasSpecialty',
    'department' : 'http://vivo.brown.edu/ontology/profile#department',
    'hospital' : 'http://vivo.brown.edu/ontology/profile#hasHospital',
    'organization' : 'http://vivo.brown.edu/ontology/profile#hasOrganization',

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

def shortIdToUri(shortId):
    return 'http://vivo.brown.edu/individual/{0}'.format(shortId)

def write_triple(sbj, pred, obj):
    return 'OPTIONAL {{ {0} {1} {2}. }}'.format(sbj, pred, obj)

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
        fac.get(property_map['credentials'], []) ]
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


@app.route('/profile/<shortId>/faculty/edit/overview/overview/update')
def profile_overview(shortId):
    data = query_faculty(shortId)
    return jsonify({'overview': data[property_map['overview']][0] })


@app.route('/profile/<shortId>/faculty/edit/research/overview/update')
def profile_research_overview(shortId):
    data = query_faculty(shortId)
    return jsonify({'research_overview': data[property_map['research_overview']][0] })


@app.route('/profile/<shortId>/faculty/edit/research/statement/update')
def profile_research_statement(shortId):
    data = query_faculty(shortId)
    return jsonify({'research_statement': data[property_map['research_statement']][0] })


@app.route('/profile/<shortId>/faculty/edit/research/funded/update')
def profile_funded_research(shortId):
    data = query_faculty(shortId)
    return jsonify({'funded_research': data[property_map['funded_research']][0] })


@app.route('/profile/<shortId>/faculty/edit/background/honors/update')
def profile_awards_honors(shortId):
    data = query_faculty(shortId)
    return jsonify({'awards_honors': data[property_map['awards_honors']][0] })


@app.route('/profile/<shortId>/faculty/edit/affiliations/affiliations/update')
def profile_affiliations(shortId):
    data = query_faculty(shortId)
    return jsonify({'affiliations': data[property_map['affiliations']][0] })

@app.route('/profile/<shortId>/faculty/edit/affiliations/collaborators/update')
def profile_collaborators(shortId):
    data = query_faculty_association(
        shortId, property_map['collaborators'])
    label = property_map['label']
    return jsonify(
        { 'research_areas':
            [ { 'rabid': k,
                'label': data[k].get(label,[''])[0] } for k in data ] })

@app.route('/profile/<shortId>/faculty/edit/teaching/overview/update')
def profile_teaching_overview(shortId):
    data = query_faculty(shortId)
    return jsonify({'teaching_overview': data[ property_map['teaching_overview']][0] })


@app.route('/profile/<shortId>/faculty/edit/research/areas/update')
def profile_research_area(shortId):
    data = query_faculty_association(
        shortId, property_map['research_areas'])
    label = property_map['label']
    return jsonify(
        { 'research_areas':
            [ { 'rabid': k,
                'label': data[k].get(label,[''])[0] } for k in data ] })

@app.route('/profile/<shortId>/faculty/edit/overview/ontheweb/update')
def profile_web_links(shortId):
    data = query_faculty_association(
        shortId, property_map['web_links'])
    text = property_map['link_text']
    url = property_map['link_url']
    rank = property_map['rank']
    return jsonify(
        { 'web_links': [ {
            'rabid': k,
            'text': data[k].get(text,[''])[0],
            'url': data[k].get(url,[''])[0],
            'rank': data[k].get(rank,[''])[0] } for k in data ] })

@app.route('/profile/<shortId>/faculty/edit/affiliations/credentials/update')
def profile_credentials(shortId):
    credential = property_map['credentials']
    props = {
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