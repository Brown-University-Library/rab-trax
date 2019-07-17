import rdflib
import json

BPROFILE = 'http://vivo.brown.edu/ontology/profile#'
VIVO = 'http://vivoweb.org/ontology/core#'
BLOCAL = 'http://vivo.brown.edu/ontology/vivo-brown/'
RDFS = 'http://www.w3.org/2000/01/rdf-schema#'


def rdf_string(data, dataType):
    if dataType == 'uri':
        return '<{}>'.format(data)
    else:
        return json.dumps(data)

class FacultyProfile:

    __property_map = {
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
        BLOCAL + 'hasGeographicResearchArea': 'geo_research_areas'
    }

    __attribute_map = {
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
        'geo_research_areas': BLOCAL + 'hasGeographicResearchArea'
    }

    __attribute_type = {
        'show_visualizations': 'boolean',
        'overview': 'literal',
        'affiliations': 'literal',
        'awards_honors': 'literal',
        'scholarly_work': 'literal',
        'research_overview': 'literal',
        'funded_research': 'literal',
        'web_links': 'web_links',
        'research_statement': 'literal',
        'teaching_overview': 'literal',
        'appointments': 'appointments',
        'collaborators': 'collaborators',
        'research_areas': 'research_areas',
        'credentials': 'credentials',
        'trainings': 'trainings',
        'delegates': 'delegates',
        'geo_research_areas': 'geo_research_areas'
    }

    def __init__(self, uri):
        self.uri = uri
        self.graph = '<http://vitro.mannlib.cornell.edu/default/vitro-kb-2>'
        self.data = {}
        self.add = set()
        self.remove = set()

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

class ResearchArea:

    __property_map = {
        VIVO + 'researchAreaOf': 'faculty',
        RDFS + 'label': 'name'
    }

    __attribute_map = {
        'faculty': VIVO + 'researchAreaOf',
        'name': RDFS + 'label'
    }

    __attribute_type = {
        'faculty': 'uri',
        'name': 'literal'
    }

    def __init__(self, uri=None):
        self.uri = uri
        self.graph = '<http://vitro.mannlib.cornell.edu/default/vitro-kb-2>'
        self.data = {}
        self.add = set()
        self.remove = set()

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