from mongoengine import Document, StringField, ListField, ReferenceField
from learning_outcomes.learning_outcome_model import Learning_Outcome
import mongo_methods

class Assignment_Mapping(Document):
    criterion_id = StringField(required=True)
    learning_outcomes = ListField(ReferenceField(Learning_Outcome))
    
    def read():
        return Assignment_Mapping.objects().to_json()
    
    def index(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return Assignment_Mapping.objects(pk=o_id)

    def delete(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return Assignment_Mapping.objects(o_id).delete()
