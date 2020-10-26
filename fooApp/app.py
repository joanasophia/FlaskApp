from flask import Flask, render_template, make_response, Response, logging, abort, jsonify, redirect
from flask import request, url_for
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import bson
import os
import sys
import json


sys.path.append(os.path.expanduser("fooApp")) # append to path to import modules
from forms import ProductForm, LoginForm
from models import User

app = Flask(__name__, static_url_path='/static')
app.config['MONGO_DBNAME'] = 'foodb'
#app.config['MONGO_URI'] = 'mongodb://localhost:27017/foodb'
app.config['MONGO_URI'] =  'mongodb+srv://joanasophia:KEY4bcn@cluster0.kavfq.gcp.mongodb.net/foodb?retryWrites=true&w=majority'
app.config['SECRET_KEY'] = 'tzU78jowks458PKs' 
app.config['SESSION_PROTECTION'] = 'strong'
login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = 'login'

mongo = PyMongo(app)

LOG = logging.create_logger(app)



@login_manager.user_loader
def load_user(user_id):
    """Flask-Login hook to load a User instance from ID."""
    u = mongo.db.users.find_one({"username": user_id})
    if not u:
        return None
    return User(u['username'])



@app.route('/')
def index():
    #return redirect(url_for('products_list'))
    return render_template('base.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('products_list'))
    form = LoginForm(request.form)
    error = None
    if request.method == 'POST' and form.validate():
        username = form.username.data.lower().strip()
        password = form.password.data.lower().strip()
        user = mongo.db.users.find_one({"username": username})
        if user and User.validate_login(user['password'], password):  
            user_obj = User(user['username'])
            login_user(user_obj)
            return redirect(url_for('products_list'))
        else:
            error = 'Incorrect username or password.'
    return render_template('user/login.html', form=form, error=error)


@app.route('/logout/')
def logout():
  logout_user()
  return redirect(url_for('products_list'))

@app.route('/products/')
def products_list():
  """Provide HTML listing of all Products."""
  # Query: Get all Products objects, sorted by date.
  products = mongo.db.products.find()[:]
  return render_template('product/index.html',
    products=products)

@app.route('/products/<product_id>/')
def product_detail(product_id):
  """Provide HTML page with a given product."""
  # Query: get Product object by ID.
  product = mongo.db.products.find_one({ "_id": ObjectId(product_id) })
  print(product)
  if product is None:
    # Abort with Not Found.
    abort(404)
  return render_template('product/detail.html',
    product=product)

@app.route('/products/<product_id>/edit/', methods=['GET', 'POST'])
@login_required
def product_edit(product_id):
    """Provide HTML form to edit a given product."""
    product = mongo.db.products.find_one({"_id": ObjectId(product_id)})
    if product is None:
        abort(404)
    form = ProductForm(request.form, data=product)
    if request.method == 'POST' and form.validate():
        mongo.db.products.replace_one(product, form.data)
        # Success. Send the user back to the detail view.
        return redirect(url_for('products_list'))
    return render_template('product/edit.html', form=form)

@app.route('/products/create/', methods=['GET', 'POST'])
@login_required
def product_create():
  """Provide HTML form to create a new product."""
  form = ProductForm(request.form)
  if request.method == 'POST' and form.validate():
    mongo.db.products.insert_one(form.data)
    #mongo.db.products.insert_one(form)
    # Success. Send user back to full product list.
    return redirect(url_for('products_list'))
  # Either first load or validation error at this point.
  return render_template('product/edit.html', form=form)


@app.route('/products/<product_id>/delete/', methods=['DELETE'])
@login_required
def product_delete(product_id):
  """Delete record using HTTP DELETE, respond with JSON."""
  result = mongo.db.products.delete_one({ "_id": ObjectId(product_id) })
  if result.deleted_count == 0:
    # Abort with Not Found, but with simple JSON response.
    response = jsonify({'status': 'Not Found'})
    response.status = 404    
    return response
  return jsonify({'status': 'OK', 'url': url_for('products_list')})


# error handler
@app.errorhandler(404)
def error_not_found(error):
  return render_template('error/not_found.html'), 404

@app.errorhandler(bson.errors.InvalidId)
def error_not_found_invalid(error):
  return render_template('error/not_found.html'), 404 


@app.route('/string/')
def return_string():
  dump = dump_request_detail(request)
  return 'Hello, world!'

@app.route('/object/')
def return_object():
  dump = dump_request_detail(request)
  headers = {'Content-Type': 'text/plain'}
  return make_response(Response('Hello, world! \n' + dump, status=200,
    headers=headers))

@app.route('/tuple/<path:resource>')
def return_tuple(resource):
  dump = dump_request_detail(request)
  return 'Hello, world! \n' + dump, 200, {'Content-Type':
    'text/plain'}


def dump_request_detail(request):
  request_detail = """
## Request INFO ##
request.endpoint: {request.endpoint}
request.method: {request.method}
request.view_args: {request.view_args}
request.args: {request.args}
request.form: {request.form}
request.user_agent: {request.user_agent}
request.files: {request.files}
request.is_xhr: {request.is_xhr}

## request.headers ##
{request.headers}
  """.format(request=request).strip()
  return request_detail


@app.before_request
def callme_before_every_request():
  # Demo only: the before_request hook.
  app.logger.debug(dump_request_detail(request))

@app.after_request
def callme_after_every_response(response):
  # Demo only: the after_request hook.
  app.logger.debug('# After Request #\n' + repr(response))
  return response


if __name__ == '__main__':
    app.run()
    