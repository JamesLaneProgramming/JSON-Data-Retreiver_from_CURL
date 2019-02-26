from flask_mongoengine import *
#http://zetcode.com/python/pymongo/
from mongoengine import DynamicDocument, StringField, IntField, BooleanField, DateTimeField

class Hubspot_Webhook(DynamicDocument):
    meta = {'collection': 'hubspot_webhooks'}

    def create(json_data):
        for each in json_data:
            hubspot_webhook = Hubspot_Webhook(**each)
            return hubspot_webhook
