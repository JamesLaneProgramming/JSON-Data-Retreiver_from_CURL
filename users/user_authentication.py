from flask import Blueprint, request, redirect, url_for, flash, render_template
from request_helper import get_redirect_target, redirect_back
from werkzeug.security import safe_str_cmp
from user_model import User
from os import environ

user_authentication_blueprint = Blueprint('user_authentication_blueprint', __name__)

@user_authentication_blueprint.route('/login', methods=['GET','POST'])
def login():
    if(request.method == 'POST'):
        try:
            username = str(request.values.get('username'))
            password = str(request.values.get('password'))
        except Exception as error:
            print(error)
            next = get_redirect_target()
            return redirect(url_for('login'), next=next)
        else:
            #Inform users of username/password constrains.
            if(safe_str_cmp(username.encode('utf-8'), password.encode('utf-8'))):
                user = User.authenticate(username, password)
                if user is not None and user.is_authenticated:
                    login_status = login_user(user)
                    #http://flask.pocoo.org/docs/1.0/patterns/flashing/
                    flash('Logged in successfully.')
                    next = get_redirect_target()
                    return redirect_back('home', next=next)
                else:
                    next = get_redirect_target()
                    return redirect_back('signup', next=next)
            else:
                next = get_redirect_target()
                return redirect_back('login', next=next)
    else:
        return render_template('login.html')

@user_authentication_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@user_authentication_blueprint.route('/signup', methods=['GET', 'POST'])
def signup():
    if(request.method == 'POST'):
        try:
            username = str(request.form['username'])
            password = str(request.form['password'])
            safeword = str(request.form['safeword'])
            next = get_redirect_target()
        except Exception as error:
            raise error
        else:
            if username is not "" or password is not "" or safeword is not "" and \
                    safe_str_cmp(username.encode('utf-8'), password.encode('utf-8'), safeword.encode('utf-8')):
                if(User.objects(username=username)):
                    flash("Username already taken")
                    return redirect(url_for('signup', next=next))
                elif(safeword == str(environ.get('safeword'))):
                    new_user = User.create(username.encode('utf-8'), password.encode('utf-8'))
                    User.authenticate(username, password)
                    return redirect_back('home', next=next)
                else:
                    flash("safeword was incorrect, could not create account")
                    return redirect(url_for('signup', next=next))
            else:
                flash("username, password or safeword cannot be empty")
                return redirect(url_for('signup', next=next))
    else:
        return render_template('signup.html')
