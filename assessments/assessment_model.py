from mongoengine import Document, IntField ReferenceField, ListField

class Assessment(Document):
    criteria = ListField(ReferenceField('Criterion'))

    def index(id):
        return Assessment.objects(id).first()

    def create(criteria):
        assessment = Assessment(criteria)
        return assessment

class Criterion(Document):
    criterion_id = IntField()
    criterion_points = IntField()
    criterion_comments = ListField(StringField())
    
    def create(criterion_id, criterion_points, criterion_comments):
        criterion = Criterion(criterion_id, criterion_points,
                              criterion_comments)
        return criterion

class Grade(Document):
    user_id = ReferenceField('User')
    learning_outcome = ReferenceField('Learning_Outcome')
    points = IntField()

class Assessment_Submission(Document):
    assessment_id = ReferenceField('Assessment')
    grades = ListField(ReferenceField('Grade'))
