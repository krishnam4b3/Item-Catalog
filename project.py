from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Brand, Product, User
# Import Login session
from flask import session as login_session
import random
import string
# imports for gconnect
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
# import login decorator
from functools import wraps
from flask import Flask, render_template,
request, redirect, jsonify, url_for, flash
app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog"

engine = create_engine('sqlite:///brand.db')
Base.metadata.bind = engine


DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_name' in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@app.route('/login')
def showlogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application-json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # upgrade the authorization code in credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failedto upgrade\n
                                            the authorization code'), 401)
        response.headers['Content-Type'] = 'application-json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'POST')[1].decode("utf-8"))
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
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response
    # Access token within the app
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user\n
                                            is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    response = make_response(json.dumps('Succesfully connected users'), 200)

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # See if user exists or if it doesn't make a new one
    print('User email is' + str(login_session['email']))
    user_id = getUserID(login_session['email'])
    if user_id:
        print('Existing user#' + str(user_id) + 'matches this email')
    else:
        user_id = createUser(login_session)
        print('New user_id#' + str(user_id) + 'created')
        login_session['user_id'] = user_id
        print('Login session is tied to :id#' + str(login_session['user_id']))

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 200px; height: 200px;border-radius:100px;- \
      webkit-border-radius:100px;-moz-border-radius: 100px;">'
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output

# Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).first()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).first()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).first()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session.
@app.route('/gdisconnect')
def gdisconnect():
    # only disconnect a connected User
    access_token = login_session.get('access_token')
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s'%
    login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is')
    print(result)
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke\n
                                            token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/logout')
def logout():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            del login_session['user_id']
            del login_session['provider']
            flash("you have succesfully been logout")
            return redirect(url_for('showBrands'))
    else:
        flash("you were not logged in")
        return redirect(url_for('showBrands'))


@app.route('/brand/<int:brand_id>/product/JSON')
def brandProductJSON(brand_id):
    brand = session.query(Brand).filter_by(id=brand_id).one()
    details = session.query(Product).filter_by(
        brand_id=brand_id).all()
    return jsonify(Product=[i.serialize for i in items])


@app.route('/brand/<int:brand_id>/details/<int:details_id>/JSON')
def productsJSON(brand_id, details_id):
    Product_Details = session.query(Product).filter_by(id=details_id).one()
    return jsonify(Product_Details=Product_Details.serialize)


@app.route('/brand/JSON')
def brandsJSON():
    brands = session.query(Brand).all()
    return jsonify(brands=[r.serialize for r in brands])
# Show all brands


@app.route('/')
@app.route('/brand/')
def showBrands():
    session1 = DBSession()
    brands = session1.query(Brand).all()
    # return "This page will show all my brands"
    session1.close()
    return render_template('brands.html', brands=brands)


# Create a new brand
@app.route('/brand/new/', methods=['GET', 'POST'])
def newBrand():
    session2 = DBSession()
    if request.method == 'POST':
        newBrand = Brand(name=request.form['name'])
        session2.add(newBrand)
        session2.commit()
        session2.close()
        return redirect(url_for('showBrands'))
    else:
        session2.close()
        return render_template('newBrand.html')
    # return "This page will be for making a new brand"

# Edit a brand


@app.route('/brand/<int:brand_id>/edit/', methods=['GET', 'POST'])
def editBrand(brand_id):
    session3 = DBSession()
    editedBrand = session3.query(Brand).filter_by(id=brand_id).one()
    if request.method == 'POST':
        if request.form['name']:
            print(editedBrand.name)
            editedBrand.name = request.form['name']
            session3.add(editedBrand)
            session3.commit()
            session3.close()
            return redirect(url_for('showBrands'))
    else:
        session3.close()
        return render_template(
            'editBrand.html', brand=editedBrand)

    # return 'This page will be for editing brand %s' % brand_id

# Delete a brand


@app.route('/brand/<int:brand_id>/delete/', methods=['GET', 'POST'])
def deleteBrand(brand_id):
    session4 = DBSession()
    brandToDelete = session4.query(
        Brand).filter_by(id=brand_id).one()
    if request.method == 'POST':
        session4.delete(brandToDelete)
        session4.commit()
        session4.close()
        return redirect(
            url_for('showBrands', brand_id=brand_id))
    else:
        session4.close()
        return render_template(
            'deleteBrand.html', brand=brandToDelete)
    # return 'This page will be for deleting brand %s' % brand_id


# Show a brand product
@app.route('/brand/<int:brand_id>/')
@app.route('/brand/<int:brand_id>/product/')
def showProduct(brand_id):
    session5 = DBSession()
    brand = session5.query(Brand).filter_by(id=brand_id).one()
    details = session5.query(Product).filter_by(brand_id=brand_id).all()
    session5.close()
    for d in details:
        print(d.name)
    return render_template('product.html', details=details, brand=brand)
    # return 'This page is the product for brand %s' % brand_id

# Create a new product details


@app.route(
    '/brand/<int:brand_id>/product/new/', methods=['GET', 'POST'])
def newProduct(brand_id):
    session6 = DBSession()
    if request.method == 'POST':
        newDetails = Product(name=request.form['name'],
                             description=request.form[
                             'description'], price=request.form['price'],
                             costumetype=request.form['costumetype'],
                             brand_id=brand_id)
        session6.add(newItem)
        session6.commit()
        session6.close()

        return redirect(url_for('showProduct', brand_id=brand_id))
    else:
        session6.close()
        return render_template('newProduct.html', brand_id=brand_id)

    return render_template('newProduct.html', brand=brand)
    # return 'This page is for making a new product details for brand %s'
    # %brand_id

# Edit a product details


@app.route('/brand/<int:brand_id>/product/<int:product_id>/edit',
           methods=['GET', 'POST'])
def editProduct(brand_id, product_id):
    session7 = DBSession()
    editedProduct = session7.query(Product).filter_by(id=product_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedProduct.name = request.form['name']
        if request.form['description']:
            editedProduct.description = request.form['name']
        if request.form['price']:
            editedProduct.price = request.form['price']
        if request.form['costumetype']:
            editedProduct.costumetype = request.form['costumetype']
        session7.add(editedProduct)
        session7.commit()
        session7.close()
        return redirect(url_for('showProduct', brand_id=brand_id))
    else:
        session7.close()

        return render_template('editProduct.html', brand_id=brand_id,
                               product_id=product_id, details=editedProduct)

    # return 'This page is for editing product details %s' % product_id

# Delete a product details


@app.route('/brand/<int:brand_id>/product/<int:product_id>/delete',
           methods=['GET', 'POST'])
def deleteProduct(brand_id, product_id):
    session8 = DBSession()
    productToDelete = session8.query(Product).filter_by(id=product_id).one()
    if request.method == 'POST':
        session8.delete(productToDelete)
        session8.commit()
        session8.close()
        return redirect(url_for('showProduct', brand_id=brand_id))
    else:
        session8.close()
        return render_template('deleteProduct.html', details=productToDelete)
    # return "This page is for deleting product details %s" % product_id


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
