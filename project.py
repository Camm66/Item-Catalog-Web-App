from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CatalogItem

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/home')
def showHome():
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template("homepage.html", categories=categories)

@app.route('/login')
def loginPage():
    return "Welcome to the Login Page"

@app.route('/addCategory', methods=['GET', 'POST'])
def addCategory():
    if request.method == 'POST':
        if request.form['name']:
            newCategory = Category(name=request.form['name'])
            session.add(newCategory)
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
            session.commit()
        return redirect(url_for("showHome"))
    else:
        return render_template("editcategory.html", category=editedCategory)

@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    deletedCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        session.delete(deletedCategory)
        session.commit()
        return redirect(url_for('showHome'))
    return render_template('deletecategory.html', category=deletedCategory)

@app.route('/category/<int:category_id>')
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(CatalogItem).filter_by(category_id=category.id).all()
    return render_template("categorypage.html", category=category, items=items)

@app.route('/<string:category_name>/<string:item_name>')
def showItem():
    return "show item"

@app.route('/<string:category_name>/<string:item_name>/addItem')
def addItem():
    return "add item"

@app.route('/<string:category_name>/<string:item_name>/editItem')
def editItem():
    return "edit item"

@app.route('/<string:category_name>/<string:item_name>/deleteItem')
def deleteItem():
    return "delete item"




if __name__ == '__main__':
    app.secret_key = 'secretkey'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
