from mongoengine import Document, IntField
import mongo_methods

class Enrollment(Document):
    canvas_course_id = IntField(required=True)
    canvas_user_id = IntField(required=True)

    def read():
        return Enrollment.objects().to_json()
    
    def index(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return Enrollment.objects(pk=o_id)

    def delete(id):
        o_id = mongo_methods.generate_objectid_from_string(id)
        return Enrollment.objects(o_id).delete()
