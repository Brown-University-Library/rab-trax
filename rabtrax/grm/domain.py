

class Model(type):
    def __init__(cls, classname, bases, dct_):
        super().__init__(classname, bases, dct_)


def domain(ontologies):
    ns_map = { o.name: o for o in ontologies }
    return Model('Resource', (object,) , { 'ontologies': ns_map })



class Domain:

    def __init__(self, store=None):
        self.store = store
        self.resources = {}

    def setStore(self, store):
        self.store = store