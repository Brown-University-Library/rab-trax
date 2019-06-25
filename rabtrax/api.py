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
    'web_links': 'http://vivo.brown.edu/ontology/vivo-brown/drrbWebPage',
    'link_text': 'http://vivoweb.org/ontology/core#linkAnchorText',
    'link_url': 'http://vivoweb.org/ontology/core#linkURI',
    'rank': 'http://vivoweb.org/ontology/core#rank',

    'teacherFor': 'http://vivo.brown.edu/ontology/vivo-brown/teacherFor',
    'citation#contributorTo': 'http://vivo.brown.edu/ontology/citation#contributorTo',
    'core#educationalTraining': 'http://vivoweb.org/ontology/core#educationalTraining',
    'hasGeographicResearchArea': 'http://vivo.brown.edu/ontology/vivo-brown/hasGeographicResearchArea',
    'lastName': 'http://xmlns.com/foaf/0.1/lastName',
    'core#hasCollaborator': 'http://vivoweb.org/ontology/core#hasCollaborator',
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
    'profile#hasTraining': 'http://vivo.brown.edu/ontology/profile#hasTraining',
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
    if data:
        return jsonify(
            { 'web_links': [ {
                'rabid': k,
                'text': data[k].get(text,[''])[0],
                'url': data[k].get(url,[''])[0],
                'rank': data[k].get(rank,[''])[0] } for k in data ] })