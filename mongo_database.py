from pymongo import MongoClient

#Connects to the MongoDB database
mongo_client = MongoClient('mongodb://localhost:27017/')
#Attempt to reference database and create if not exists
integration_db = mongo_client.canvas_integration
users_collection = integration_db.users
users_collection.insert({"username": "James", "Password": "123"})

print(users_collection.find_one({"username": "James"}))
