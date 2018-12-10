from pymongo import MongoClient
from os import environ

def mongo_client():
    #Connects to the MongoDB database
    mongo_client = MongoClient('ds125684.mlab.com:25684', 
            username        = 'James', 
            password        = environ.get('mongoDB_Password'), 
            authSource      = 'canvas_integration', 
            authMechanism   = 'SCRAM-SHA-1')
    return mongo_client
