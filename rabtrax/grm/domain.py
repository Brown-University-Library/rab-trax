import rdflib


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


class Resource(type):
    def __init__(cls, classname, bases, dct_):
        super().__init__(classname, bases, dct_)


def domain(ontologies):
    ns_map = { o.name: o for o in ontologies }
    return Resource('Resource', (object,) , { 'ontologies': ns_map })



class Property:

    def __init__(self, store=None):
        self.store = store
        self.resources = {}

    def setStore(self, store):
        self.store = store