from mongoengine import Document, StringField, ListField, ReferenceField
from learning_outcomes.learning_outcome_model import Learning_Outcome

class Subject(Document):
    subject_name = StringField(required=True)
    subject_description = StringField()
    learning_outcomes = ListField(ReferenceField('learning_outcomes'))
    
    def read():
        return Subject.objects()
