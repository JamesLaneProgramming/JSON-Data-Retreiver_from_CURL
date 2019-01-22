from mongoengine import Document, StringField, IntField, FloatField, ReferenceField, ListField
from learning_outcomes.learning_outcome_model import Learning_Outcome
from users.user_model import User

class Assessment(Document):
    criteria = ListField(ReferenceField('Criterion'))
    
    def index(id):
        return Assessment.objects(id).first()

    def create(criteria):
        assessment = Assessment(criteria)
        return assessment

    def load_from_json(assessment_json_data):
        pass
        #Loop json and extract criterion data
        #Create criterion
        #Save to database

class Criterion(Document):
    criterion_name = StringField()
    criterion_description = StringField()
    criterion_points = FloatField()
    criterion_learning_outcomes = ListField(ReferenceField(Learning_Outcome))

    def read():
        return Criterion.objects()
    def index(id):
        return Criterion.objects(pk=id)
    def map_learning_outcomes(learning_outcomes):
        criterion_learning_outcomes = learning_outcomes

class Grade(Document):
    user_id = ReferenceField(User)
    learning_outcome = ReferenceField(Learning_Outcome)
    canvas_outcome_id = StringField()
    points = FloatField()

    def canvas_outcome_mapped_to_learning_outcome():
        pass

class Assessment_Submission(Document):
    user_id = ReferenceField(User)
    assessment_id = ReferenceField(Assessment)
    grades = ListField(ReferenceField(Grade))
