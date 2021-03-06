import rdflib
import json

BPROFILE = 'http://vivo.brown.edu/ontology/profile#'
VIVO = 'http://vivoweb.org/ontology/core#'
BLOCAL = 'http://vivo.brown.edu/ontology/vivo-brown/'
RDFS = 'http://www.w3.org/2000/01/rdf-schema#'
RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'

def rdf_string(data, dataType):
    if dataType == 'uri':
        return '<{}>'.format(data)
    elif dataType == 'dateTime':
        return '"{}"^^<http://www.w3.org/2001/XMLSchema#dateTime>'.format(
            data.strftime('%Y-%m-%dT%H:%M:%S.%f'))
    else:
        return json.dumps(data)

class FacultyProfile:

    __property_map = {
        BLOCAL + 'profileUpdated': 'last_updated',
        BPROFILE + 'consentsVisualizations': 'show_visualizations',
        VIVO + 'overview': 'overview',
        BLOCAL + 'affiliations': 'affiliations',
        BLOCAL + 'awardsAndHonors': 'awards_honors',
        BLOCAL + 'scholarlyWork': 'scholarly_work',
        VIVO + 'researchOverview': 'research_overview',
        BLOCAL + 'fundedResearch': 'funded_research',
        BLOCAL + 'drrbWebPage': 'web_links',
        BLOCAL + 'researchStatement': 'research_statement',
        VIVO + 'teachingOverview': 'teaching_overview',
        BPROFILE + 'hasAppointment': 'appointments',
        VIVO + 'hasCollaborator': 'collaborators',
        VIVO + 'hasResearchArea': 'research_areas',
        BPROFILE + 'hasCredential': 'credentials',
        BPROFILE + 'hasTraining': 'trainings',
        BLOCAL + 'hasDelegate': 'delegates',
        BLOCAL + 'hasGeographicResearchArea': 'geo_research_areas',
        RDF + 'type': 'rdfType'
    }

    __attribute_map = {
        'last_updated': BLOCAL + 'profileUpdated',
        'show_visualizations': BPROFILE + 'consentsVisualizations',
        'overview': VIVO + 'overview',
        'affiliations': BLOCAL + 'affiliations',
        'awards_honors': BLOCAL + 'awardsAndHonors',
        'scholarly_work': BLOCAL + 'scholarlyWork',
        'research_overview': VIVO + 'researchOverview',
        'funded_research': BLOCAL + 'fundedResearch',
        'web_links': BLOCAL + 'drrbWebPage',
        'research_statement': BLOCAL + 'researchStatement',
        'teaching_overview': VIVO + 'teachingOverview',
        'appointments': BPROFILE + 'hasAppointment',
        'collaborators': VIVO + 'hasCollaborator',
        'research_areas': VIVO + 'hasResearchArea',
        'credentials': BPROFILE + 'hasCredential',
        'trainings': BPROFILE + 'hasTraining',
        'delegates': BLOCAL + 'hasDelegate',
        'geo_research_areas': BLOCAL + 'hasGeographicResearchArea',
        'rdfType': RDF + 'type'
    }

    __attribute_type = {
        'last_updated': 'dateTime',
        'show_visualizations': 'boolean',
        'overview': 'literal',
        'affiliations': 'literal',
        'awards_honors': 'literal',
        'scholarly_work': 'literal',
        'research_overview': 'literal',
        'funded_research': 'literal',
        'web_links': 'uri',
        'research_statement': 'literal',
        'teaching_overview': 'literal',
        'appointments': 'appointments',
        'collaborators': 'uri',
        'research_areas': 'uri',
        'credentials': 'credentials',
        'trainings': 'trainings',
        'delegates': 'delegates',
        'geo_research_areas': 'geo_research_areas',
        'rdfType': 'uri'
    }

    def __init__(self, uri):
        self.uri = uri
        self.graph = '<http://vitro.mannlib.cornell.edu/default/vitro-kb-2>'
        self.data = {}
        self.add = set()
        self.remove = set()
        for p in self.__property_map:
            self.__dict__[self.__property_map[p]] = []
        self.update('rdfType', [ VIVO + 'FacultyMember' ] )

    def load(self, data):
        for d in data:
            if d in self.__property_map:
                self.__dict__[self.__property_map[d]] = data[d]
                self.data[d] = data[d]

    def format_triple(self, attr, data):
        return ( rdf_string(self.uri, 'uri'),
            rdf_string(self.__attribute_map[attr], 'uri'),
            rdf_string(data, self.__attribute_type[attr]) )

    def update(self, attr, data):
        if data == getattr(self, attr):
            return
        add = { self.format_triple(attr, d) for d in data }
        rmv = { self.format_triple(attr, d) for d in getattr(self, attr) }
        self.add |= (add - rmv)
        self.remove |= (rmv - add)
        setattr(self, attr, data)

    def to_dict(self):
        return { a: self.__dict__.get(a, []) for a in self.__attribute_map }


class ResearchArea:

    __property_map = {
        VIVO + 'researchAreaOf': 'faculty',
        RDFS + 'label': 'name',
        RDF + 'type': 'rdfType'
    }

    __attribute_map = {
        'faculty': VIVO + 'researchAreaOf',
        'name': RDFS + 'label',
        'rdfType': RDF + 'type'
    }

    __attribute_type = {
        'faculty': 'uri',
        'name': 'literal',
        'rdfType': 'uri'
    }

    def __init__(self, uri=None):
        self.uri = uri
        self.graph = '<http://vitro.mannlib.cornell.edu/default/vitro-kb-2>'
        self.data = {}
        self.add = set()
        self.remove = set()
        for p in self.__property_map:
            self.__dict__[self.__property_map[p]] = []
        self.update('rdfType', [ BLOCAL + 'ResearchArea' ] )

    def load(self, data):
        for d in data:
            try:
                self.__dict__[self.__property_map[d]] = data[d]
                self.data[d] = data[d]
            except:
                continue

    def format_triple(self, attr, data):
        return ( rdf_string(self.uri, 'uri'),
            rdf_string(self.__attribute_map[attr], 'uri'),
            rdf_string(data, self.__attribute_type[attr]) )

    def update(self, attr, data):
        if data == getattr(self, attr):
            return
        add = { self.format_triple(attr, d) for d in data }
        rmv = { self.format_triple(attr, d) for d in getattr(self, attr) }
        self.add |= (add - rmv)
        self.remove |= (rmv - add)
        setattr(self, attr, data)

    def to_dict(self):
        return { a: self.__dict__.get(a, []) for a in self.__attribute_map }


class WebLink:

    __property_map = {
        BLOCAL + 'drrbWebPageOf': 'faculty',
        VIVO + 'linkAnchorText': 'link_text',
        VIVO + 'linkURI': 'link_address',
        VIVO + 'rank': 'rank',
        RDFS + 'label': 'name',
        RDF + 'type': 'rdfType'
    }

    __attribute_map = {
        'faculty': BLOCAL + 'drrbWebPageOf',
        'link_text': VIVO + 'linkAnchorText',
        'link_address': VIVO + 'linkURI',
        'rank': VIVO + 'rank',
        'name': RDFS + 'label',
        'rdfType': RDF + 'type'
    }

    __attribute_type = {
        'faculty': 'uri',
        'link_text': 'literal',
        'link_address': 'literal',
        'rank': 'literal',
        'name': 'literal',
        'rdfType': 'uri'
    }

    def __init__(self, uri=None):
        self.uri = uri
        self.graph = '<http://vitro.mannlib.cornell.edu/default/vitro-kb-2>'
        self.data = {}
        self.add = set()
        self.remove = set()
        for p in self.__property_map:
            self.__dict__[self.__property_map[p]] = []
        self.update('rdfType', [ VIVO + 'URLLink' ] )

    def load(self, data):
        for d in data:
            try:
                self.__dict__[self.__property_map[d]] = data[d]
                self.data[d] = data[d]
            except:
                continue

    def format_triple(self, attr, data):
        return ( rdf_string(self.uri, 'uri'),
            rdf_string(self.__attribute_map[attr], 'uri'),
            rdf_string(data, self.__attribute_type[attr]) )

    def update(self, attr, data):
        if data == getattr(self, attr):
            return
        add = { self.format_triple(attr, d) for d in data }
        rmv = { self.format_triple(attr, d) for d in getattr(self, attr) }
        self.add = self.add - rmv
        self.add |= (add - rmv)
        self.remove = self.remove - add
        self.remove |= (rmv - add)
        setattr(self, attr, data)

    def to_dict(self):
        return { a: self.__dict__.get(a, []) for a in self.__attribute_map }


class Collaborator:

    __property_map = {
        BLOCAL + 'fullName': 'full_name',
        BLOCAL + 'alphaName': 'alpha_name',
        RDFS + 'label': 'label',
        RDF + 'type': 'rdfType'
    }

    __attribute_map = {
        'full_name': BLOCAL + 'fullName',
        'alpha_name': BLOCAL + 'alphaName',
        'label': RDFS + 'label',
        'rdfType': RDF + 'type'
    }

    __attribute_type = {
        'full_name': 'literal',
        'alpha_name': 'literal',
        'label': 'literal',
        'rdfType': 'uri'
    }

    def __init__(self, uri=None):
        self.uri = uri
        self.graph = '<http://vitro.mannlib.cornell.edu/default/vitro-kb-2>'
        self.data = {}
        self.add = set()
        self.remove = set()
        for p in self.__property_map:
            self.__dict__[self.__property_map[p]] = []
        self.update('rdfType', [ VIVO + 'FacultyMember' ] )

    def load(self, data):
        for d in data:
            try:
                self.__dict__[self.__property_map[d]] = data[d]
                self.data[d] = data[d]
            except:
                continue

    def format_triple(self, attr, data):
        return ( rdf_string(self.uri, 'uri'),
            rdf_string(self.__attribute_map[attr], 'uri'),
            rdf_string(data, self.__attribute_type[attr]) )

    def update(self, attr, data):
        if data == getattr(self, attr):
            return
        add = { self.format_triple(attr, d) for d in data }
        rmv = { self.format_triple(attr, d) for d in getattr(self, attr) }
        self.add = self.add - rmv
        self.add |= (add - rmv)
        self.remove = self.remove - add
        self.remove |= (rmv - add)
        setattr(self, attr, data)

    def to_dict(self):
        return { a: self.__dict__.get(a, []) for a in self.__attribute_map }


class Organization:

    __property_map = {
        BLOCAL + 'fullName': 'full_name',
        BLOCAL + 'alphaName': 'alpha_name',
        RDFS + 'label': 'label',
        RDF + 'type': 'rdfType'
    }

    __attribute_map = {
        'full_name': BLOCAL + 'fullName',
        'alpha_name': BLOCAL + 'alphaName',
        'label': RDFS + 'label',
        'rdfType': RDF + 'type'
    }

    __attribute_type = {
        'full_name': 'literal',
        'alpha_name': 'literal',
        'label': 'literal',
        'rdfType': 'uri'
    }

    def __init__(self, uri=None):
        self.uri = uri
        self.graph = '<http://vitro.mannlib.cornell.edu/default/vitro-kb-2>'
        self.data = {}
        self.add = set()
        self.remove = set()
        for p in self.__property_map:
            self.__dict__[self.__property_map[p]] = []
        self.update('rdfType', [ VIVO + 'FacultyMember' ] )

    def load(self, data):
        for d in data:
            try:
                self.__dict__[self.__property_map[d]] = data[d]
                self.data[d] = data[d]
            except:
                continue

    def format_triple(self, attr, data):
        return ( rdf_string(self.uri, 'uri'),
            rdf_string(self.__attribute_map[attr], 'uri'),
            rdf_string(data, self.__attribute_type[attr]) )

    def update(self, attr, data):
        if data == getattr(self, attr):
            return
        add = { self.format_triple(attr, d) for d in data }
        rmv = { self.format_triple(attr, d) for d in getattr(self, attr) }
        self.add = self.add - rmv
        self.add |= (add - rmv)
        self.remove = self.remove - add
        self.remove |= (rmv - add)
        setattr(self, attr, data)

    def to_dict(self):
        return { a: self.__dict__.get(a, []) for a in self.__attribute_map }