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

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key = true) #samo się generuje
    nick = db.Column(db.String(100), nullable=False)
    mail = db.Column(db.String(255), nullable=False)
    opis = db.Column(db.String(4096), nullable=True)
    zdjecie_wskaznik = db.Column(db.Integer, primary_key = true) #bazowo nie ma żadnego i ustawia ikonke podstawową





if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000,debug=True)