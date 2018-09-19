import database as db

class User():
    def __init__(self, user_id):
        self.id = user_id
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
        return self.is_authenticated
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
        return self.is_active
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
        return is_anonymous
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
        '''
        Docstring
        ---------
        get() queries the database and returns a User object.

        Arguments
        ---------
        user_id(String):
            Takes an ID of a student and returns the User object associated.

        Returns
        -------
        user(User):
            Returns a User object that is associated with the user_ID argument
        '''
        user_data = db.get_user(user_id)
        if(user_data == None):
            return None
        else:
            user = User(user_id)
            return user
    def get_user(username, password):
        '''
        Docstring
        ---------
        get_user() returns a user object based on a username/password pair.

        Arguments
        ---------
        username(String):
            Takes a String that represents a User's username
        password(String):
            Takes a String that represents a User's password

        Returns
        -------
        user(User):
            Returns a user if the username/password login pair are successful.
            Returns None otherwise.
        '''
        user_id = db.get_user_id(username, password)
        user = User(user_id)
        return user
