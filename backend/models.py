from database import execute_query_dict

class Examen:
    @classmethod
    def get_unscheduled(cls):
        query = "SELECT * FROM examens WHERE statut = 'planifié'"
        return execute_query_dict(query)

class Departement:
    def __init__(self, id, nom, code):
        self.id = id
        self.nom = nom
        self.code = code

    @classmethod
    def get_all(cls):
        query = "SELECT * FROM departements ORDER BY nom"
        return execute_query_dict(query)

    @classmethod
    def get_by_id(cls, dept_id):
        query = "SELECT * FROM departements WHERE id = %s"
        result = execute_query_dict(query, params=(dept_id,))
        return Departement(**result[0]) if result else None