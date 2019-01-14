from mongoengine import Document, ReferenceField, ListField

class Assessment(Document):
    criteria = ListField(ReferenceField('Criteria'))

    def index(id):
        return Assessment.objects(id).first()

    def create(criteria):
        assessment = Assessment(criteria)
        return assessment
