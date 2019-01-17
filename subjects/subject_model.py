from mongoengine import Document, StringField, ListField, ReferenceField

class Subject(Document):
    subject_name = StringField(required=True)
    subject_description = StringField()
    learning_outcomes = ListField(ReferenceField('learning_outcome'))
    
    def read():
        return Subject.objects()
