

class Model(type):
    def __init__(cls, classname, bases, dct_):
        type.__init__(cls, classname, bases, dct_)


def domain():
    resource_attribute_map = { 'rdf_type': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' }
    return Model('Model', (object,) , { 'lookup': resource_attribute_map })




class Domain:

    def __init__(self, store=None):
        self.store = store
        self.resources = {}

    def setStore(self, store):
        self.store = store


class RDFStatement:
    def __init__(self, sbj=None, prop=None, obj=None):
        self.sbj = sbj


