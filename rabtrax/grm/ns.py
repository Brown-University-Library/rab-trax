import rdflib


class XSDDataTypeError(Exception):
    pass


# class XSDDataType(object):

#     def __init__(self, dt):
#         self.datatype = dt

#     def validate(self, val):

#         try:
#             cls.validate(val)
#         return rdflib.Literal.__new__(cls, val, datatype=rdflib.XSD.string)  


class String(rdflib.Literal):

    def __new__(cls, val):
        return rdflib.Literal.__new__(cls, val, datatype=rdflib.XSD.string)

    def to_rdf(self):
        return self.n3()

    def __repr__(self):
        return "'{}'".format(self.value)


class Boolean(rdflib.Literal):

    def __new__(cls, val):
        return rdflib.Literal.__new__(cls, val, datatype=rdflib.XSD.boolean)

    def to_rdf(self):
        return self.n3()

    def __repr__(self):
        return "{}".format(self.value)


class DateTime(rdflib.Literal):

    def __new__(cls, val):
        return rdflib.Literal.__new__(cls, val, datatype=rdflib.XSD.dateTime)

    def to_rdf(self):
        return self.n3()

    def __repr__(self):
        return "'{}'".format(self.value)


class Integer(rdflib.Literal):

    def __new__(cls, val):
        return rdflib.Literal.__new__(cls, val, datatype=rdflib.XSD.integer)

    def to_rdf(self):
        return self.n3()

    def __repr__(self):
        return "{}".format(self.value)


class Property(object):

    def __init__(self, uri, range_):
        # self.uri = 
        self.range_ = range_

    def validate(self, val):
        try:
            return self.range_(val)
        except DataTypeError as e:
            print(e)

    def triple(self, sbj, val):
        return (sbj, self.uri, rval)




class Ontology(object):

    def __init__(self, namespace, prefix):
        self.prefix = prefix
        self.name = prefix
        self.ns = rdflib.Namespace(namespace)
        self.properties = set()
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