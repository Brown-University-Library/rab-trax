class Ontology(object):

    def __init__(self, namespace, prefix):
        self.prefix = prefix
        self.name = prefix
        self.ns = namespace
        self.properties = {}
        self.classes = set()


RDF = Ontology('http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'rdf')
RDF.properties = {
    'type': RDF.ns + 'type'
}

RDFS = Ontology('http://www.w3.org/2000/01/rdf-schema#', 'rdfs')
RDFS.properties = {
    'label': RDFS.ns + 'label'
}

VIVO = Ontology('http://vivoweb.org/ontology/core#', 'vivo')
VIVO.properties = {
    'overview': VIVO.ns + 'overview',
    'research_overview': VIVO.ns + 'researchOverview',
    'teaching_overview': VIVO.ns + 'teachingOverview',
    'has_collaborator': VIVO.ns + 'hasCollaborator',
    'has_research_area': VIVO.ns + 'hasResearchArea',
}
VIVO.classes = {
    VIVO.ns + 'Faculty'
}

BPROFILE = Ontology('http://vivo.brown.edu/ontology/profile#', 'bprofile')
BPROFILE.properties = {
    'consents_visualizations': BPROFILE.ns + 'consentsVisualizations',
    'has_appointment': BPROFILE.ns + 'hasAppointment',
    'has_credential': BPROFILE.ns + 'hasCredential',
    'has_training': BPROFILE.ns + 'hasTraining',
}

BLOCAL = Ontology('http://vivo.brown.edu/ontology/vivo-brown/', 'blocal')
BLOCAL.properties = {
    'affiliations': BLOCAL.ns + 'affiliations',
    'awards_and_honors': BLOCAL.ns + 'awardsAndHonors',
    'scholarly_work': BLOCAL.ns + 'scholarlyWork',
    'funded_research': BLOCAL.ns + 'fundedResearch',
    'drrb_web_page': BLOCAL.ns + 'drrbWebPage',
    'research_statement': BLOCAL.ns + 'researchStatement',
    'has_delegate': BLOCAL.ns + 'hasDelegate',
    'has_geographic_research_area': BLOCAL.ns + 'hasGeographicResearchArea'
}