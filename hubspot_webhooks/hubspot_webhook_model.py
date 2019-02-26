from flask_mongoengine import *
#http://zetcode.com/python/pymongo/
from mongoengine import Document, StringField, IntField, BooleanField, DateTimeField

class Hubspot_Webhook(Document):
    meta = {'collection': 'hubspot_webhooks'}

    def create(json_data):
        Hubspot_Webhook.insert(json_data)
