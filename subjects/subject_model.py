from mongoengine import Document, StringField, ListField, ReferenceField
from learning_outcomes.learning_outcome_model import Learning_Outcome
import mongo_methods

class Subject(Document):
    subject_code = StringField(required=True)
    subject_name = StringField(required=True)
    subject_description = StringField()
    learning_outcomes = ListField(ReferenceField(Learning_Outcome))
    
    def read():
        return Subject.objects().all_fields.to_json()
    
    def index(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return Subject.objects(pk=o_id)

    def delete(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return Subject.objects(o_id).delete()
