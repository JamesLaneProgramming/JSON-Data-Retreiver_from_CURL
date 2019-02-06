from mongoengine import Document, ListField, ReferenceField, IntField

class Rubric_Assessment(Document):
    meta = {'collection' : 'assessments'}
    user_id=IntField(required = True)
    assessment = ReferenceField('Assessment')
    grades=ListField(ReferenceField('Learning_Outcome'))

    def create(user_id, assessment, grades):
        rubric_assessment = Rubric_Assessment(user_id, assessment, grades).save()
        return assessment
    
    def delete():
        pass
