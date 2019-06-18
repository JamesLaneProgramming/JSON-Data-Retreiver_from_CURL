from mongoengine import Document, FloatField, StringField, ListField, ReferenceField
from learning_outcomes.learning_outcome_model import Learning_Outcome
import mongo_methods

class Subject_Grade(Document):
    user_id = StringField(required=True)
    grade = FloatField(required=True)

    def read():
        return Subject_Grade.objects().to_json()
    
    def index(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return Subject_Grade.objects(pk=o_id)

    def delete(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return Subject_Grade.objects(o_id).delete()
