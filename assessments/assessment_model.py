from mongoengine import Document, ListField, ReferenceField, StringField, BooleanField

class Assessment(Document):
    meta = {'collection' : 'assessments'}
    user_id=IntField(required = True, unique = True)
    grades=ListField(ReferenceField('Learning_Outcome'))

    def create(user_id, grades):
        assessment = Assessment(user_id, grades).save()
        return assessment
    def delete():
        pass
