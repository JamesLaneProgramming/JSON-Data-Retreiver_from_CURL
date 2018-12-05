from pymongo import MongoClient
from bson.objectid import ObjectId

#Connects to the MongoDB database
mongo_client = MongoClient('ds125684.mlab.com:25684')
#Attempt to reference database and create if not exists
integration_db = mongo_client.canvas_integration
users_collection = integration_db.users
#users_collection.insert({"username": "James", "password": "123"})

def get_user(username, password):
    found_user = users_collection.find_one({"username": username, "Password": password})
    return(found_user)

def get_user_by_id(_id):
    #Attempt to convert _id into an ObjectID for use with MongoDB fields
    #http://api.mongodb.com/python/current/tutorial.html#querying-by-objectid
    o_id = ObjectId(_id)
    user = users_collection.find_one({"_id": o_id})
    return user

def create_user(username, password):
    #TODO: encrypt password with hashing algorithm
    users_collection.insert({"username": username, "password": password})
