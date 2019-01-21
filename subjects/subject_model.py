from mongoengine import Document, StringField, ListField, ReferenceField
from learning_outcomes.learning_outcome_model import Learning_Outcome

class Subject(Document):
    subject_code = StringField(required=True)
    subject_name = StringField(required=True)
    subject_description = StringField()
    learning_outcomes = ListField(ReferenceField(Learning_Outcome))
    
    def read():
        return Subject.objects()
