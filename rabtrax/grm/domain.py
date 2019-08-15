import rdflib


class Attribute(object):

    def __init__(self, predUri):
        self.uri = predUri

    def __call__(self, graph):
        return [ o.toPython() for o in graph.objects(
            predicate=self.uri) ]


class Link(object):

    def __init__(self, predUri, resType):
        pass


class Resource(type):

    def __init__(cls, classname, bases, dct_):
        cls.__mapper__ = {}
        super().__init__(classname, bases, dct_)

    def __getattr__(self, key):
        if key in self.__mapper__:
            return self.__mapper__[key](self.graph)

    def __setattr__(cls, key, value):
        if isinstance(value, Attribute):
            cls.__mapper__[key] = value
        else:
            type.__setattr__(cls, key, value)



def domain(ontologies):
    ns_map = { o.name: o for o in ontologies }
    return Resource('Resource', (object,) , { 'ontologies': ns_map })


class Description(object):

    def __init__(self, vocabularies):
        pass


# class Property:

#     def __init__(self, store=None):
#         self.store = store
#         self.resources = {}

#     def setStore(self, store):
#         self.store = store