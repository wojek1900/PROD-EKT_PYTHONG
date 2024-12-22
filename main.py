import os
from flask import Flask, request, render_template, redirect, url_for
from flask_security import Security, UserMixin, RoleMixin, SQLAlchemyUserDatastore,current_user, login_required
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
### Urzytkownik ###
# id
# nick (nick musi być unikatowy)
# mail
# hasło
# opis (przekirowywać do swjej strony)
# zdjencie profilowe
### koniec urzytkownika ###
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY','developerskie')
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT', 'jakas-sol')
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
db = SQLAlchemy(app)




class User(db.Model):
    id = db.Column(db.Integer, primary_key = True) #samo się generuje
    nick = db.Column(db.String(100), nullable=False)
    mail = db.Column(db.String(255), nullable=False)
    opis = db.Column(db.String(4096), nullable=True)
    zdjecie_wskaznik = db.Column(db.Integer, primary_key = True) #bazowo nie ma żadnego i ustawia ikonke podstawową


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")
@app.route("/register")
def register():
    return render_template("register.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000,debug=True)