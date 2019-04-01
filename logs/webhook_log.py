#www.python.org/dev/peps/pep-0328/
from mongoengine import (Document, StringField, ListField, ReferenceField
import mongo_methods

class Webhook_Log(Document):
    webhook_receive_date_time = DateField(
    subject_name = StringField(required=True)
    subject_description = StringField()
    learning_outcomes = ListField(ReferenceField(Learning_Outcome))
    
    def read():
        return Subject.objects().to_json()
    
    def index(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        print(o_id)
        return Subject.objects(pk=o_id)

    def delete(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return Subject.objects(o_id).delete():
