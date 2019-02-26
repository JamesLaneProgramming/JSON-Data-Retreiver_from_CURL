from flask_mongoengine import *
import json
#http://zetcode.com/python/pymongo/
from mongoengine import DynamicDocument, StringField, IntField, BooleanField, DateTimeField

class Hubspot_Webhook(DynamicDocument):
    meta = {'collection': 'hubspot_webhooks'}

    def create(json_data):
        for each in json_data:
            json_element = json.loads(each)
            hubspot_webhook = Hubspot_Webhook(**json_element).save()
            return hubspot_webhook
