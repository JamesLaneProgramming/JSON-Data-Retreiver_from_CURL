from mongoengine import Document, IntField, StringField, DateTimeField, EmailField
import mongo_methods

class Hubspot_Request(Document):
    course_id = IntField(required=True)
    section_id = IntField(required=True)
    canvas_user_first_name = StringField()
    canvas_user_last_name = StringField()
    canvas_user_email_address = EmailField()

    def read():
        return Hubspot_Request.objects().to_json()

    def index(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return Hubspot_Request.objects(pk=o_id)

    def delete(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return Hubspot_Request.objects(o_id).delete()
