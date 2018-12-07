from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from os import environ

#Connects to the MongoDB database
mongo_client = MongoClient('ds125684.mlab.com:25684', 
        username='James', 
        password=environ.get('mongoDB_Password'), 
        authSource='canvas_integration', 
        authMechanism='SCRAM-SHA-1')
#Attempt to reference database and create if not exists
integration_db = mongo_client.canvas_integration
users_collection = integration_db.users
#users_collection.insert({"username": "James", "password": "123"})

def get_user(username, password):
    #TODO: Sanitise inputs before query database 
    assert isinstance(username, str)
    assert isinstance(password, str)
    #Generate a password hash for database storage.
    password_hash = generate_password_hash(password)
    found_user = users_collection.find_one({"Username": username, "Password": password_hash})
    return(found_user)

def get_user_by_id(_id):
    #Attempt to convert _id into an ObjectID for use with MongoDB fields
    #http://api.mongodb.com/python/current/tutorial.html#querying-by-objectid
    #Note: Sometimes you will need to delete your session tokens in order for the o_id to not be None(Resulting in errors)
    #TODO: What validation needs to be done here?
    try:
        o_id = ObjectId(_id)
        user = users_collection.find_one({"_id": o_id})
        return user
    except bson.errors.InvalidId as error:
        raise Invalid_Session_Token("Session ID is None. Cannot construct ObjectId")
    except Exception as error:
        raise error

def create_user(username, password):
    #TODO: encrypt password with hashing algorithm
    assert isinstance(username, str)
    assert isinstance(password, str)
    password_hash = generate_password_hash(password)
    users_collection.insert({"Username": username, "Password": password_hash})

class Invalid_Session_Token(Exception):
    pass
