from flask import Flask
from db.db import create_db
app = Flask(__name__)

app.secret_key = b'_dssdlkj323232#""#/' #it is just here so we can show flash message to the user (normally checking secrets into git is not a very good idea)

from blueprints.admin.admin import admin_bp
from blueprints.userside.userside import userside_bp
from blueprints.admin_users.admin_users import admin_users_bp

create_db() #creating db (if it does not exist. Delete db file and reload app if structure has changes)

#registering blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(userside_bp)
app.register_blueprint(admin_users_bp)

if __name__ == '__main__':
    app.run(debug=True)