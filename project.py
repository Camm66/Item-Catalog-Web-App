from flask import (Flask, render_template, request,
                   redirect, url_for, jsonify,
                   flash, send_from_directory)
from flask import session as login_session
from flask import make_response
from flask_wtf.csrf import CSRFProtect
from functools import wraps
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CatalogItem, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from werkzeug.utils import secure_filename
import json
import os
import random
import string
import httplib2
import requests


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "ItemCatalogWebDB"


# Initialize the database
engine = create_engine('sqlite:///catalog.db?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Image handling storage location
UPLOAD_FOLDER = '/vagrant/ItemCatalog/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 # Max file == 2 Megabytes


# Image handling helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_file(request):
        file = request.files['pic']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return filename


def delete_image(filename):
    return os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))


@app.route('/images/<string:filename>')
def get_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


# JSON APIs to view Catalog Information
@app.route('/JSON')
def categoriesJSON():
    Categories = session.query(Category).all()
    return jsonify(Categories=[category.serialize for category in Categories])


@app.route('/category/<int:category_id>/JSON')
def categoryJSON(category_id):
    items = session.query(CatalogItem).filter_by(category_id=category_id).all()
    return jsonify(Category_Items=[item.serialize for item in items])


@app.route('/item/<int:item_id>/JSON')
def itemJSON(item_id):
    Item = session.query(CatalogItem).filter_by(id=item_id).one_or_none()
    return jsonify(Item=[Item.serialize])


# Authentication page
@app.route('/login')
def showLogin():
    # Create anti-forgery state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# Decorator function used to check for authorization before page access
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You are not allowed to access there")
            return redirect('/login')
    return decorated_function


@app.route('/gconnect', methods=['POST'])
def gconnect():
    '''
    Method: login a user via the google+ oauth api
    Args:
        arg1(login_session): global login_session object
        arg2(state_token): anti-forgery state token created in showLogin method
    Returns:
        return login_session object populated with user information returned
        from the google server
    '''
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px; height: 300px;border-radius: 150px;
    -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '''
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    '''
    Method: login a user via the facebook oauth api
    Args:
        arg1(login_session): global login_session object
        arg2(state_token): anti-forgery state token created in showLogin method
    Returns:
        return login_session object populated with user information returned
        from the facebook server
    '''
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = (('https://graph.facebook.com/oauth/access_token?grant_type='
            'fb_exchange_token&client_id=%s&client_secret=%s&'
            'fb_exchange_token=%s')
           % (app_id, app_secret, access_token))
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    userinfo_url = "https://graph.facebook.com/v2.8/me"
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = (('https://graph.facebook.com/v2.8/me?access_token=%s&'
            'fields=name,id,email' % token))
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    login_session['access_token'] = token

    url = (('https://graph.facebook.com/v2.8/me/picture?access_token=%s&'
            'redirect=0&height=200&width=200' % token))
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px; height: 300px;border-radius: 150px;
    -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '''

    flash("Now logged in as %s" % login_session['username'])
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    '''
    Method: call google+ api to revoke the access_token
    Args:
        arg1(login_session): global login_session object
        arg2(access_token): stored in login_session['access_token']
    '''
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('disconnect'))
    else:
        response = make_response(json.dumps('Token revocation error.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/fbdisconnect')
def fbdisconnect():
    '''
    Method: call facebook api to revoke the access_token
    Args:
        arg1(login_session): global login_session object
        arg2(access_token): stored in login_session['access_token']
    '''
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = '''https://graph.facebook.com/%s/permissions?
    access_token=%s''' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


# Disconnect based on Oauth provider
@app.route('/disconnect')
def disconnect():
    '''
    Method: clear user information from current login_session
    Args:
        arg1(login_session), global login_session object
    Returns:
        1) Calls disconnect method for the provider (google, facebook)
        2) Redirect to the showHome method
    '''
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showHome'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showHome'))


# User Helper Functions
# Create a new user based on the results of an Oauth request
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(
           email=login_session['email']).one_or_none()
    return user.id


# Retrieve a user enter from the User table
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one_or_none()
    return user


# Retrieve a user id from the User table
def getUserID(email):
    user = session.query(User).filter_by(email=email).one_or_none()
    return user.id


# Method calls for each page:
@app.route('/')
@app.route('/home')
def showHome():
    '''
    Method: Render the home page with all Categories and latest 8 CatalogItems
    Args:
        args: None
    Returns:
        return rendered homepage.html
    '''
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(CatalogItem).order_by(CatalogItem.id.desc()).limit(8)
    return render_template("homepage.html", categories=categories,
                           items=items, login_session=login_session)


@app.route('/category/<int:category_id>')
def showCategory(category_id):
    '''
    Method: Show all nested CatalogItems in a selected Category
    Args:
        arg1(int): category_id, unique id for the selected Category
    Returns:
        return rendered categorypage.html page with all related items
    '''
    category = session.query(Category).filter_by(id=category_id).one_or_none()
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(CatalogItem).filter_by(category_id=category_id).all()
    return render_template("categorypage.html", categories=categories,
                           category=category, items=items,
                           login_session=login_session)


@app.route('/addCategory', methods=['GET', 'POST'])
@login_required
def addCategory():
    '''
    Method: add a Category to the database
    Args:
        args: none
    Returns:
        for GET:
            Render addcategory.html page
        for POST:
            Add the category and redirect to showHome method
    '''
    if request.method == 'POST':
        if request.form['name']:
            user_id = getUserID(login_session['email'])
            newCategory = Category(name=request.form['name'], user_id=user_id)
            session.add(newCategory)
            flash('New Category %s Successfully Created' % newCategory.name)
            session.commit()
        return redirect(url_for("showHome"))
    else:
        return render_template("addcategory.html")


@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def editCategory(category_id):
    '''
    Method: edit a Category in the database
    Args:
        arg1(int): category_id, unique id for the selected category
    Returns:
        for GET:
            Render editcategory.html page
        for POST:
            Edit the Category and redirect to the showCategory method
    '''
    editedCategory = session.query(Category).filter_by(
                     id=category_id).one_or_none()
    if editedCategory.user_id != login_session['user_id']:
        flash("You don't have permission to edit that item!")
        return redirect(url_for("showHome"))
    if request.method == 'POST':
        if request.form['name'] != editedCategory.name:
            editedCategory.name = request.form['name']
            session.add(editedCategory)
            flash('Category %s Successfully Updated' % editedCategory.name)
            session.commit()
        return redirect(url_for("showCategory", category_id=category_id))
    else:
        return render_template("editcategory.html", category=editedCategory,
                               login_session=login_session)


@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_id):
    '''
    Method: delete a Category from the database
    Args:
        arg1(int): category_id, unique id for the selected category
    Returns:
        for GET:
            Render deletecategory.html page
        for POST:
            Delete the Category and redirect to showHome method
    '''
    deletedCategory = session.query(Category).filter_by(
                      id=category_id).one_or_none()
    if deletedCategory.user_id != login_session['user_id']:
        flash("You don't have permission to delete that item!")
        return redirect(url_for("showHome"))
    if request.method == 'POST':
        session.delete(deletedCategory)
        flash('Category %s Successfully deleted' % deletedCategory.name)
        session.commit()
        return redirect(url_for('showHome'))
    return render_template('deletecategory.html', category=deletedCategory,
                           login_session=login_session)


@app.route('/item/<int:item_id>')
def showItem(item_id):
    '''
    Method: render the page for a selected CatalogItem
    Args:
        arg1(int): item_id, unique item id
    Returns:
        return itempage.html populated with the CatalogItem information
    '''
    categories = session.query(Category).order_by(asc(Category.name))
    item = session.query(CatalogItem).filter_by(id=item_id).one_or_none()
    return render_template('itempage.html', item=item, categories=categories,
                           login_session=login_session)


@app.route('/item/<int:category_id>/addItem', methods=['GET', 'POST'])
@login_required
def addItem(category_id):
    '''
    Method: add a CatalogItem in the database
    Args:
        arg1(int): category_id, parent category for the new item
    Returns:
        for GET:
            Renders HTML template for the additem.html page
        for POST:
            Adds item to database and redirects to showCategory method
    '''
    category = session.query(Category).filter_by(id=category_id).one_or_none()
    if request.method == 'POST':
        if request.form['name']:
            user_id = getUserID(login_session['email'])
            if(request.form['pic']):
                filename = upload_file(request)
                newItem = CatalogItem(name=request.form['name'],
                                      description=request.form['description'],
                                      category_id=category.id,
                                      picture=filename, user_id=user_id)
            else:
                newItem = CatalogItem(name=request.form['name'],
                                      description=request.form['description'],
                                      category_id=category.id, user_id=user_id)
            session.add(newItem)
            flash('Item %s Successfully Created' % newItem.name)
            session.commit()
        return redirect(url_for('showCategory', category_id=category.id))
    return render_template('additem.html', category_id=category_id,
                           login_session=login_session)


@app.route('/item/<int:category_id>/<int:item_id>/edit',
           methods=['GET', 'POST'])
@login_required
def editItem(category_id, item_id):
    '''
    Method: edit a CatalogItem in the database
    Args:
        arg1(int): category_id, parent category for the item
        arg2(int): item_id, unique item id
    Returns:
        for GET:
            Renders HTML template for the edititem.html page
        for POST:
            Edits item in database and redirect to showCategory method
    '''
    item = session.query(CatalogItem).filter_by(id=item_id).one_or_none()
    if item.user_id != login_session['user_id']:
        flash("You don't have permission to edit that item!")
        return redirect(url_for("showHome"))
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        session.add(item)
        flash('Item %s Successfully Updated' % item.name)
        session.commit()
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('edititem.html', category_id=category_id,
                               item=item, login_session=login_session)


@app.route('/item/<int:category_id>/<int:item_id>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteItem(category_id, item_id):
    '''
    Method: delete a CatalogItem from database
    Args:
        arg1(int): category_id, parent category for the item
        arg2(int): item_id, unique item id
    Returns:
        for GET:
            Renders HTML template for the deleteitem.html page
        for POST:
            Removes item and redirects to showHome method
    '''
    item = session.query(CatalogItem).filter_by(id=item_id).one_or_none()
    if item.user_id != login_session['user_id']:
        flash("You don't have permission to delete that item!")
        return redirect(url_for("showHome"))
    if request.method == 'POST':
        session.delete(item)
        if(item.picture):
            delete_image(item.picture)
        flash('Item %s Successfully Deleted' % item.name)
        session.commit()
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('deleteitem.html', category_id=category_id,
                               item=item, login_session=login_session)


if __name__ == '__main__':
    app.secret_key = 'secretkey'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
