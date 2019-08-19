from rabtrax.grm.domain import domain, Attribute
from rabtrax.grm import ns

Resource = domain([ns.BLOCAL, ns.BPROFILE, ns.VIVO, ns.RDF, ns.RDFS])

import rdflib
import inspect


BPROFILE = rdflib.Namespace("http://vivo.brown.edu/ontology/profile#")


class FacultyProfile(Resource):

    print("Hanging out!")
    # __rdfType__ = ns.VIVO.classes

    # last_updated = Property()
    show_visualizations = Attribute(BPROFILE.consentsVisualizations)
    # print(__name__)
    # print(inspect.getmembers())
    # overview = dm.Property(dm.string)
    # affiliations = dm.Property(dm.string)
    # awards_honors = dm.Property(dm.string)
    # scholarly_work = dm.Property(dm.string)
    # research_overview = dm.Property(dm.string)
    # funded_research = dm.Property(dm.string)
    # web_links = dm.Property(WebLink)
    # research_statement = dm.DataProperty(dm.string)
    # teaching_overview = dm.DataProperty(dm.string)

    # appointments = dm.ObjectProperty(Appointment)
    # collaborators = dm.ObjectProperty(Collaborator)
    # research_areas = dm.ObjectProperty(ResearchArea)
    # credentials = dm.ObjectProperty(
    #     BPROFILE.hasCredential, relationship=Credential)
    # trainings = dm.ObjectProperty(ResearchArea)
    # delegates': 'delegates',
    # geo_research_areas': 'geo_research_areas',

    def __init__(self, graph):
        self.uri = list(graph.subjects())[0]
        self.graph = graph

    # def show_visualizations(self):
    #     return [ o.toPython() for o in self.graph.objects(
    #         predicate=BPROFILE.consentsVisualizations) ]