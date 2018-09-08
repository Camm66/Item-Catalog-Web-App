from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_from_directory
from flask import session as login_session
from flask import make_response
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CatalogItem
from werkzeug.utils import secure_filename
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
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

#Initialize the database

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#Added CSRF protection

csrf = CSRFProtect()
csrf.init_app(app)

@app.before_request
def csrf_protect():#
#    if request.method == "POST":
#        token = session.pop('csrf_token')
#        if not token or token != request.form.get('csrf_token'):
#            abort(400)
    return

def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = some_random_string()
    return session['csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token


#Image handling
UPLOAD_FOLDER = '/vagrant/ItemCatalog/images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

#JSON APIs to view Catalog Information
@app.route('/JSON')
def categoriesJSON():
    Categories = session.query(Category).all()
    return jsonify(Categories=[category.serialize for category in Categories])

@app.route('/category/<int:category_id>/JSON')
def categoryJSON(category_id):
    Category_Items = session.query(CatalogItem).filter_by(category_id=category_id).all()
    return jsonify(Category_Items=[item.serialize for item in Category_Items])

@app.route('/item/<int:item_id>/JSON')
def itemJSON(item_id):
    Item = session.query(CatalogItem).filter_by(id=item_id).one()
    return jsonify(Item=[Item.serialize])











#Authentication
#Google auth API
@app.route('/gconnect', methods=['POST'])
def gconnect():
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
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
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
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output

    # User Helper Functions

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                       'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
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
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response








#Method calls for each page:

@app.route('/')
@app.route('/home')
def showHome():
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template("homepage.html", categories=categories)

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

@app.route('/category/<int:category_id>')
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(CatalogItem).filter_by(category_id=category_id).all()
    return render_template("categorypage.html", category=category, items=items)

@app.route('/addCategory', methods=['GET', 'POST'])
def addCategory():
    if request.method == 'POST':
        if request.form['name']:
            newCategory = Category(name=request.form['name'])
            session.add(newCategory)
            flash('New Category %s Successfully Created' % newCategory.name)
            session.commit()
        return redirect(url_for("showHome"))
    else:
        return render_template("addcategory.html")

@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['name'] != editedCategory.name:
            editedCategory.name = request.form['name']
            session.add(editedCategory)
            flash('Category %s Successfully Updated' % editedCategory.name)
            session.commit()
        return redirect(url_for("showCategory", category_id=category_id))
    else:
        return render_template("editcategory.html", category=editedCategory)

@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    deletedCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        session.delete(deletedCategory)
        flash('Category %s Successfully deleted' % deletedCategory.name)
        session.commit()
        return redirect(url_for('showHome'))
    return render_template('deletecategory.html', category=deletedCategory)

@app.route('/item/<int:item_id>')
def showItem(item_id):
    item = session.query(CatalogItem).filter_by(id=item_id).one()
    return render_template('itempage.html', item=item)

@app.route('/item/<int:category_id>/addItem', methods=['GET', 'POST'])
def addItem(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    if request.method =='POST':
        if request.form['name']:
            filename = upload_file(request)
            newItem = CatalogItem(name=request.form['name'],
                description=request.form['description'], category_id=category.id, picture=filename)
            session.add(newItem)
            flash('Item %s Successfully Created' % newItem.name)
            session.commit()
        return redirect(url_for('showCategory', category_id=category.id))
    return render_template('additem.html', category_id=category_id)

@app.route('/item/<int:category_id>/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    item = session.query(CatalogItem).filter_by(id=item_id).one()
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
        return render_template('edititem.html', item=item)

@app.route('/item/<int:category_id>/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    item = session.query(CatalogItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(item)
        delete_image(item.picture)
        flash('Item %s Successfully Deleted' % item.name)
        session.commit()
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('deleteitem.html', item=item)


if __name__ == '__main__':
    app.secret_key = 'secretkey'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
