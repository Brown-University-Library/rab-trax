BPROFILE = 'http://vivo.brown.edu/ontology/profile#'
VIVO = 'http://vivoweb.org/ontology/core#'
BLOCAL = 'http://vivo.brown.edu/ontology/vivo-brown/'

class FacultyProfile:

    __property_map = {
        BPROFILE + 'consentsVisualizations': 'show_visualizations',
        VIVO + 'overview': 'overview',
        BLOCAL + 'affiliations': 'affiliations',
        BLOCAL + 'awardsAndHonors': 'awards',
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

    def __init__(self, uri):
        self.uri = uri

    def load(self, data):
        for d in data:
            if d in self.__property_map:
                self.__dict__[self.__property_map[d]] = data[d]