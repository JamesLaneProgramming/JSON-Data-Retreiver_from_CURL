from pymongo import MongoClient

#Connects to the MongoDB database
mongo_client = MongoClient('mongodb://localhost:27017/')
#Attempt to reference database and create if not exists
integration_db = mongo_client.canvas_integration
users_collection = integration_db.users
#users_collection.insert({"username": "James", "password": "123"})

def get_user(username, password):
    found_user = users_collection.find_one({"username": username, "Password": password})
    return(found_user)

def get_user_by_id(_id):
    return users_collection.find_one({"_id": _id})
