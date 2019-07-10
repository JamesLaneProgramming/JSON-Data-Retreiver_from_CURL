import bson
from bson.objectid import ObjectId

#Attempt to convert _id into an ObjectID for use with MongoDB fields
#http://api.mongodb.com/python/current/tutorial.html#querying-by-objectid
def generate_objectid_from_string(objectid_string):
    try:
        o_id = ObjectId(objectid_string)
    except Exception as error:
        raise error
    else:
        return o_id
