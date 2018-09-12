import database as db

class User():
    def __init__(self, user_id):
        user.id = user_id
    @property
    def is_authenticated(self):
        '''
        Docstring: is_authenticated() checks whether the user's credetials
        are valid. is_authenticated() must equate to True as a criteria of
        login_required().
        Returns
        -------
        is_authenticated(Bool):
            Returns True if the user has provided valid credentials.
            Returns False if the user's credentials are invalid.
        '''
        return True
    @property
    def is_active(self):
        '''
        Docstring: is_active checks whether the user's account has special
        restrictions in place. For example, if the account has been suspended.
        Returns
        -------
        is_active(Bool):
            Returns True if the user's account is active(No restrictions in
            place).
            Returns False if the user's account has been
            deactivated(Restrictions in place).
        '''
        return True
    @property
    def is_anonymous(self):
        '''
        Docstring: If particular functionality does not require an
        authenticated User, is_anonymous() may be useful.
        Returns
        -------
        is_anonymous(Bool):
            Returns True if the user is an anonymous user.
            Returns False if the user is authenticated.
        '''
        return False
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
        try:
            return str(user_id)
        except AttributeError as error:
            error
        except Exception as error:
            print("Could not convert user id to unicode ID")
            raise error
    def get(user_id):
        #gets a specific user from the database with the id.
        user_data = db.get_user(user_id)
        if(user_data == None):
            return None
        else:
            user = User(user_id)
            return user
    def get_user(username, password):
        user_id = db.get_user_id(username, password)
        user = User(user_id)
        user.is_authenticated = True
        return user
