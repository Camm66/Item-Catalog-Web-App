from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/home')
def showHome():
    return "Welcome to the Home Page!"

@app.route('/login')
def loginPage():
    return "Welcome to the Login Page"

@app.route('/addCategory')
def addCategory():
    return "add"

@app.route('/editCategory')
def editCategory():
    return "edit"

@app.route('/deletecategory')
def deleteCategory():
    return "delete"

@app.route('/<string:category_name>')
def showCategory():
    return "show category"

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
