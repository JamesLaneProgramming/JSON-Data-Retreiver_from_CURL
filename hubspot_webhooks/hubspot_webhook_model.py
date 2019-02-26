from flask_mongoengine import *
import json
#http://zetcode.com/python/pymongo/
from mongoengine import DynamicDocument, StringField, IntField, BooleanField, DateTimeField

class Hubspot_Webhook(DynamicDocument):
    meta = {'collection': 'hubspot_webhooks'}

    def create(json_data):
        hubspot_webhook = Hubspot_Webhook(**json_data)
        return hubspot_webhook
