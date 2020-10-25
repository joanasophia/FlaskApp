from flask_script import Manager
from flask import url_for
from fooApp.app import app

manager = Manager(app)
app.config['DEBUG'] = True # Ensure debugger will load.
#app.config['SERVER_NAME'] = "localhost:5000"

# with app.app_context(), app.test_request_context():
#     url_for('static', filename='/static/Indo')

if __name__ == '__main__':
  manager.run()