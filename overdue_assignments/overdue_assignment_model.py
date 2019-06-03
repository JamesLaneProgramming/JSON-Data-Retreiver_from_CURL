from mongoengine import Document, IntField, StringField, DateTimeField, BooleanField
import mongo_methods

class Overdue_Assignment(Document):
    couse_id = IntField(required=True)
    assignment_id = IntField(required=True)
    user_id = IntField(required=True)
    due_date = DateTimeField()
    date_added = DateTimeField()
    extension = BooleanField()
    extension_date = DateTimeField()
    
    def read():
        return Overdue_Assignment.objects().to_json()

    def index(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return Overdue_Assignment.objects(pk=o_id)

    def delete(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return Overdue_Assignment.objects(o_id).delete()
