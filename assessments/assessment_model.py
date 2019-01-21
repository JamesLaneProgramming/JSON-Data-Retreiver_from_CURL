from mongoengine import Document, IntField ReferenceField, ListField

class Assessment(Document):
    criteria = ListField(ReferenceField('Criterion'))

    def index(id):
        return Assessment.objects(id).first()

    def create(criteria):
        assessment = Assessment(criteria)
        return assessment

class Criterion(Document):
    criterion_assessment = ReferenceField(Assessment)
    criterion_points = IntField()
    criterion_comments = ListField(StringField())
    criterion_mapping_id = IntField()

    def read():
        Criterion.objects()
    def index(id):
        Criterion.objects(pk=id)
class Grade(Document):
    user_id = ReferenceField('User')
    learning_outcome = ReferenceField('Learning_Outcome')
    points = IntField()

class Assessment_Submission(Document):
    assessment_id = ReferenceField('Assessment')
    grades = ListField(ReferenceField('Grade'))
