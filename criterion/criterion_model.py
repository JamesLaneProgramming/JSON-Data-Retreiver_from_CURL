from mongoengine import Document, StringField, ListField, ReferenceField
from learning_outcomes.learning_outcome_model import Learning_Outcome
import mongo_methods

class Criterion(Document):
    criterion_id = StringField(required=True)
    learning_outcomes = ReferenceField(Learning_Outcome)
    
    def read():
        return Criterion.objects().to_json()
    
    def index(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        print(o_id)
        return Criterion.objects(pk=o_id)

    def delete(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return criterion.objects(o_id).delete()
