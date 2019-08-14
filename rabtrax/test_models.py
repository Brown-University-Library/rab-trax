from grm.domain import domain
from grm import ns

Resource = domain([ns.BLOCAL, ns.BPROFILE, ns.VIVO, ns.RDF, ns.RDFS])

class FacultyProfile(Resource):

    __rdfType__ = ns.VIVO.classes

    uri = dm.Attribute(dm.URI, unique=True)
    last_updated = dm.Property(dm.dateTime)
    show_visualizations = dm.Property(dm.boolean)
    overview = dm.Property(dm.string)
    affiliations = dm.Property(dm.string)
    awards_honors = dm.Property(dm.string)
    scholarly_work = dm.Property(dm.string)
    research_overview = dm.Property(dm.string)
    funded_research = dm.Property(dm.string)
    web_links = dm.ObjectProperty(WebLink)
    research_statement = dm.DataProperty(dm.string)
    teaching_overview = dm.DataProperty(dm.string)

    appointments = dm.ObjectProperty(Appointment)
    collaborators = dm.ObjectProperty(Collaborator)
    research_areas = dm.ObjectProperty(ResearchArea)
    credentials = dm.ObjectProperty(
        BPROFILE.hasCredential, relationship=Credential)
    trainings = dm.ObjectProperty(ResearchArea)
    delegates': 'delegates',
    geo_research_areas': 'geo_research_areas',

    def __init__(self):
        pass