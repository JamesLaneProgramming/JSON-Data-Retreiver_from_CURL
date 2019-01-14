from mongoengine import Document, IntField, FloatField, StringField

class Learning_Outcome(Document):
    meta = {'collection': 'learning_outcomes'}
    learning_outcome_id = IntField()
    learning_outcome_name = StringField()
    learning_outcome_description = StringField()
    
    def index(id):
        return Learning_Outcome.objects(learning_outcome_id=id).first()
