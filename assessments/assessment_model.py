from mongoengine import Document, StringField, BooleanField

class Assessment(Document):
    meta = {'collection' : 'assessments'}
    user_id=StringField(required = True, unique = True)
    grades=StringField(required = True)

    def create(user_id, grades):
        assessment = Assessment(user_id, grades).save()
        return assessment
