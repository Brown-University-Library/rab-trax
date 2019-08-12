import rdflib
import SPARQLWrapper


class Graph:

    def __init__(self, queryAddr, updateAddr, email, passwd):
        self.triples = rdflib.Graph()
        self.remote = SPARQLWrapper.SPARQLWrapper(queryAddr, updateAddr)
        self.remote.addParameter('email', email)
        self.remote.addParameter('password', passwd)
        self.remote.setMethod(SPARQLWrapper.POST)
        self.id_map = {}

    def query(self, resource):
        q = Query(resource, self)
        return q

    def executeQuery(self, query):
        self.remote.setQuery(qText.format(''.join(uriValues)))
        results = self.remote.queryAndConvert()

    def update(self, uText):
        pass

class Query:

    def __init__(self, resource, graph):
        self.resource = resource
        self.graph = graph
        self.filters = []
        self.qtext = ''


    def first(self):
        self.graph.executeQuery(self)


    def all(self):
        pass


    def get(self, uri):
        self.qtext = "DESCRIBE {}".format(uri)


    def filter_by(self, **kwargs):
        self.qtext = "DESCRIBE ?uri WHERE{{{0}}}"