import os
from flask_login import current_user
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_security import Security, UserMixin, RoleMixin, SQLAlchemyUserDatastore
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', 'developerskie')
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT', 'jakas-sol')
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nick = db.Column(db.String(100), nullable=False, unique=True)
    mail = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    opis = db.Column(db.String(4096), nullable=True)
    zdjecie_wskaznik = db.Column(db.Integer, default=0)
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    active = db.Column(db.Boolean(), default=True)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.fs_uniquifier:
            self.fs_uniquifier = str(uuid.uuid4())

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/index.html")
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login.html", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        
        user = User.query.filter((User.mail == identifier) | (User.nick == identifier)).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main'))
        else:
            flash('Nieprawidłowe dane logowania.')
    
    return render_template("login.html")

@app.route("/register.html", methods=['GET'])
def register():
    return render_template("register.html")

@app.route("/main.html")
@login_required
def main():
    return render_template("main.html", user=current_user)

@app.route('/add_user', methods=['POST'])
def add_user():
    nick = request.form.get('nick')
    mail = request.form.get('mail')
    password = request.form.get('password')
    print(f"nick: {nick}, mail: {mail}, password: {password}")

    if not nick or not mail or not password:
        flash('Wszystkie pola są wymagane.')
        return redirect(url_for('register'))

    try:
        # Sprawdź czy użytkownik już istnieje
        if User.query.filter((User.mail == mail) | (User.nick == nick)).first():
            flash('Email lub nick już istnieje.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(
            nick=nick,
            mail=mail,
            password=hashed_password,
            opis="",
            fs_uniquifier=str(uuid.uuid4()),
            active=True  # Dodaj tę linię
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Przypisz rolę "user" do nowego użytkownika
        user_role = user_datastore.find_role("user")
        user_datastore.add_role_to_user(new_user, user_role)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('main'))
    except Exception as e:
        db.session.rollback()
        print(f"Błąd podczas rejestracji: {e}")
        flash('Wystąpił błąd podczas rejestracji.')
        return redirect(url_for('register'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == "__main__":
    with app.app_context():
        # Utwórz nową bazę danych
        db.create_all()
        
        if not user_datastore.find_role("user"):
            user_datastore.create_role(name="user", description="Normal user")
            db.session.commit()
            
    app.run(host='0.0.0.0', port=5000, debug=True)
    
    
################################################################
# co trzeba zrobić, aby ładnie wyglądało:
# - naprawić aby flask działał z Ajaxem
# - ulepszyć wyglląd main.html
# - dodać ładne przejście ajaxowe z animacjom po zalogowaniu
# - dodać animacje wejścia na profil urzytkownika (animacja nieskończona nawet nieajaxowo)
# - urzyć zwykłych przejść ajaxowych w innych zakładkach
# - przywrócić system particle pozbywając się problemu z zapychaniemie pamięci oraz dodać opcje kliknięcia aby zmienić mouseForce na -10
################################################################
# co zrobić aby wszystko działało:
# - dodać sprawdzanie danych w formularzach rejestracji i logowania nick nie może mieć @
# - dodać opcję edycji opisu i zdjęcia w profilu użytkownika
# - zrobić wyszukiwarkę po nicku
# - zrobić bazy danych do wszystkich wiadomości które bedą zlinkowane z innymi bazami danych do koemntarzy
# - dodać opcję usuwania wiadomości
# - dodać opcję edycji wiadomości
# - dodać opcję zmiany hasła
# - dodać opcję zmiany maila
# - dodać opcję zmiany nicku
# - dodać opcję usuwania konta
# - dodać opcję zmiany avatara
# - dodać opcję pobierania avatara
# - dodać opcję robienia grup
# - dodać opcję dołączenia do grup
# - dodać opcję usuwania z grup
# - dodać opcje pisania wiadomości do urzytkowników w grupach i prywatnych
# - opcje wysyłania plików, filmów, zdjęć do wiadomości
# - powiadomienia o nowych wiadomościach
# - zlinkowanie AI jak llama czy qwen do analizy komentarzy i danych
# - zrobienie wykresów z danych postów
# - zrobienie wyszukiwarki po tagach
# - dodać tło main z particlejs z configu
# - jak wszystko się uda sprubować urzywając tensorflowa wybierać trafne treści dla urzytkownika
###
