from os import environ
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import bson
from bson.objectid import ObjectId

class User():
    authenticated = False
    active = False
    anonymous = False
    id = None
    
    #Connects to the MongoDB database
    mongo_connection = MongoClient('ds125684.mlab.com:25684', 
            username        = 'James', 
            password        = environ.get('mongoDB_Password'), 
            authSource      = 'canvas_integration', 
            authMechanism   = 'SCRAM-SHA-1')

    def is_authenticated(self):
        return authenticated
    def is_active(self):
        return active
    def is_anonymous(self):
        return anonymous
    def __init__(self):
        pass
        #authenticate(username, password)
    def load_user_details(self, user_details):
        self.id = user_details['_id']
    def authenticate(self, username, password):
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
        assert isinstance(username, str)
        assert isinstance(password, str)
        #Generate a password hash for database storage.
        found_user = mongo_connection.users.find_one({"Username": username})
        if found_user:
            if check_password_hash(password, found_user['Password']):
                return(found_user)
            else:
                print("Wrong password")
                return None
        else:
            print("No user with that username found")
            return None
    '''
    Docstring: is_authenticated() checks whether the user's credetials
    are valid. is_authenticated() must equate to True as a criteria of
    login_required().
    Returns
    -------
    is_authenticated(Bool):
        Returns True if the user has provided valid credentials.
        Returns False if the user's credentials are invalid.

    Docstring: is_active checks whether the user's account has special
    restrictions in place. For example, if the account has been suspended.
    Returns
    -------
    is_active(Bool):
        Returns True if the user's account is active(No restrictions in
        place).
        Returns False if the user's account has been
        deactivated(Restrictions in place).
    
    Docstring: If particular functionality does not require an
    authenticated User, is_anonymous() may be useful.
    Returns
    -------
    is_anonymous(Bool):
        Returns True if the user is an anonymous user.
        Returns False if the user is authenticated.
    '''
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
        return str(self.id)

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
        #Note: Sometimes in development you will need to delete your session tokens in order for the o_id to not be None(Resulting in errors)
        try:
            o_id = ObjectId(_id)
            user = db.users.find_one({"_id": o_id})
            return user
        except bson.errors.InvalidId as error:
            raise error
        except Exception as error:
            raise error
        
    def create(username, password):
        assert isinstance(username, str)
        assert isinstance(password, str)
        password_hash = generate_password_hash(password)
        user_details = mongo_connection.users.insert({"Username": username, "Password": password_hash})

        if(user_details != None):
            user = User()
            user.load_user_details(user_details)
            return user
