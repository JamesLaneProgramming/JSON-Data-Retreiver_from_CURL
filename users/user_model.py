from os import environ
import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import bson
from bson.objectid import ObjectId
from flask_mongoengine import *
#http://zetcode.com/python/pymongo/
from mongoengine import Document, StringField, IntField, BooleanField, \
DateTimeField, ListField, ReferenceField

class User(UserMixin, Document):
    '''
    Docstring
    ---------
    The User class is used to authenticated requests and authorise actions to be performed in the application.
    '''
    meta = {'collection': 'users'}
    username = StringField(required = True, unique=True)
    password = StringField(required = True)
    authenticated = BooleanField(default = False)
    anonymous = BooleanField(default = False)
    active = BooleanField(default = True)
    hubspot_refresh_token = StringField()
    hubspot_access_token_expiry = IntField()
    last_hubspot_access_token_refresh = DateTimeField()

    def is_authenticated(self):
        '''
        Docstring
        ---------
        is_authenticated() checks whether the user has successfully logged in using valid credentials. is_authenticated() must equate to True as a criteria of
        login_required().

        Returns
        -------
        authenticated(Bool):
            Returns True if the user has successfully authenticated with valid credentials. Returns False if the user has failed to authenticate.
        '''
        return self.authenticated

    def is_active(self):
        '''
        Docstring
        ---------
        is_active checks whether the user's account has special restrictions in place. For example, if the account has been suspended.

        Returns
        -------
        active(Bool):
            Returns True if the user's account is active(No restrictions in place). Returns False if the user's account has been deactivated(Restrictions in place).
        '''
        return self.active

    def is_anonymous(self):
        '''
        Docstring
        ---------
        is_anonymous checks whether the current user is anonymous. Some webapps will allow anonymous use. If particular functionality does not require an authenticated User, is_anonymous() may be useful.

        Returns
        -------
        anonymous(Bool):
            Returns True if the user is an anonymous user. Returns False if the user is authenticated.
        '''
        return self.anonymous

    def authenticate(username, password):
        '''
        Docstring
        ---------
        Takes in a username, password pair and queries the database for a potential user.
        Arguments
        ---------
        username(String):
            Takes a String function argument to represent a user's username
        password(String):
            Takes a String function argument to represent a user's password
        Returns
        -------
        found_user(Dict):
            Returns a user Dict if the username, password pair matches a user credentials in the database.
        None(None):
            Returns None if the username was not found in the database or if the password asociated with a user is incorrect
        '''
        #TODO: Sanitise inputs before query database
        try:
            username = str(username)
            password = str(password)
        except Exception as error:
            raise error
        else:
            user = User.objects(username=username).first()
            if user:
                if check_password_hash(user.password, password):
                    user.authenticated = True
                    user.save()
                    return(user)
                else:
                    print("User could not be authenticated.")
                    return None
            else:
                print("No user with that username found")
                return None

    def get_id(self):
        '''
        Docstring
        ---------
        get_id() returns the Unicode ID of the User.

        Returns
        -------
        ID(Unicode String):
            The ID associated with the User account.
        '''
        #TODO: Encode user id as unicode string
        return str(self.pk)

    def get(_id):
        '''
        Docstring
        ---------
        Retrieves a user from the database from a _id stored in the session upon successful login.

        Arguments
        ---------
        _id(string):
            Takes a String function argument to query the database with.

        Returns
        -------
        user(Dict):
            Returns user from the database if _id matches a user document.
        '''
        #Attempt to convert _id into an ObjectID for use with MongoDB fields
        #http://api.mongodb.com/python/current/tutorial.html#querying-by-objectid
        try:
            o_id = ObjectId(_id)
            user = User.objects(pk = o_id).first()
            return user
        except bson.errors.InvalidId as error:
            #Session ID is None and therefor throws InvalidId error.
            return None
        except Exception as error:
            raise error

    def set_hubspot_refresh_token(user_id, refresh_token):
        user = User.get(user_id)
        user.update(hubspot_refresh_token=refresh_token)
        user.save()
        return user

    def set_hubspot_access_token_expiry(user_id, access_token_expiry):
        user = User.get(user_id)
        user.update(hubspot_access_token_expiry=access_token_expiry)
        user.update(last_hubspot_access_token_refresh=datetime.datetime.utcnow())
        user.save()
        return user

    def create(username, password):
        password_hash = generate_password_hash(password)
        try:
            created_user = User(username, password_hash).save()
        except mongoengine.errors.NotUniqueError as error:
            return "Username already taken"
        except Exception as error:
            pass
        return created_user
    '''
    def encode_auth_token(user_id):

        Docstring
        ---------
        Returns
        -------
        auth_token(String):
            Returns a User Auth Token.

        try:
            payload = {
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=365, seconds=0),
                    'iat': datetime.datetime.utcnow(),
                    'sub': user_id
                    }
            return jwt.encode(
                    payload,
                    app.config.get('SECRET_KEY'),
                    algorithm='HS256'
                    )
        except Exception as error:
            return e
    '''
