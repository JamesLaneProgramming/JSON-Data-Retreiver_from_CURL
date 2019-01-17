from mongoengine import Document
from mongoengine import ReferenceField, IntField, StringField
import bson
from bson.objectid import ObjectId

class Learning_Outcome(Document):
    meta = {'collection': 'learning_outcomes'}
    learning_outcome_name = StringField()
    learning_outcome_description = StringField()
    
    def index(learning_outcome_id):
        #Attempt to convert _id into an ObjectID for use with MongoDB fields
        #http://api.mongodb.com/python/current/tutorial.html#querying-by-objectid
        try:
            o_id = ObjectId(learning_outcome_id)
        except Exception as error:
            raise error
        return Learning_Outcome.objects(pk=o_id).first()
    
    def read():
        return Learning_Outcome.objects().to_json()
