from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CatalogItem
import json

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#Added CSRF protection
@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = some_random_string()
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

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

#Method calls for each page:

@app.route('/')
@app.route('/home')
def showHome():
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template("homepage.html", categories=categories)

@app.route('/login')
def loginPage():
    return "Welcome to the Login Page"

@app.route('/category/<int:category_id>')
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(CatalogItem).filter_by(category_id=category.id).all()
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
            newItem = CatalogItem(name=request.form['name'],
                description=request.form['description'], category_id=category.id)
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
        flash('Item %s Successfully Deleted' % item.name)
        session.commit()
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('deleteitem.html', item=item)


if __name__ == '__main__':
    app.secret_key = 'secretkey'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
