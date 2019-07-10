#www.python.org/dev/peps/pep-0328/
from mongoengine import (Document, StringField, ListField, ReferenceField,
        DateTimeField, URLField)
import mongo_methods

class Webhook_Log(Document):
    webhook_receive_date_time = DateTimeField(default=datetime.utcnow)
    webhook_sender = URLField()
    
    def read():
        return Webhook_Log.objects().to_json()
    
    def index(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return Webhook_Log.objects(pk=o_id)

    def delete(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return Webhook_Log.objects(o_id).delete():
