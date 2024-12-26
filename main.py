import os
import time
import logging
from werkzeug.utils import secure_filename
from flask_login import current_user
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_security import Security, UserMixin, RoleMixin, SQLAlchemyUserDatastore
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', 'developerskie')
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT', 'jakas-sol')
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
    zdjecie_wskaznik = db.Column(db.String(255), nullable=False, default='static/basics/profile.png')
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    active = db.Column(db.Boolean(), default=True)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.fs_uniquifier:
            self.fs_uniquifier = str(uuid.uuid4())
        if not self.zdjecie_wskaznik:
            self.zdjecie_wskaznik = 'basics/profile.png'

class PostAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('public_post.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(1024), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    post = db.relationship('public_post', back_populates='post_attachments')

class public_post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(4096), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    isprivate = db.Column(db.Boolean(), default=False)
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    author = db.relationship('User', backref=db.backref('posts', lazy=True))
    post_attachments = db.relationship('PostAttachment', back_populates='post', cascade="all, delete-orphan")
    def __init__(self, **kwargs):
        super(public_post, self).__init__(**kwargs)
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
    return render_template("main.html", user=current_user, posts=public_post.query.filter_by(isprivate=False).order_by(public_post.created_at.desc()).all())

@app.route("/profile.html")
@login_required
def profile():
    return render_template("profile.html", user=current_user)


@app.route("/change_profile", methods=['POST'])
@login_required
def change_profile():
    if request.method == 'POST':
        new_user = User.query.get(current_user.id)
        changes = request.form.to_dict()

        if 'nick' in changes:
            new_nick = changes['nick']
            if new_nick != new_user.nick:
                existing_user = User.query.filter_by(nick=new_nick).first()
                if existing_user:
                    flash('Ten nick jest już zajęty.')
                    return redirect(url_for('profile'))
                new_user.nick = new_nick

        if 'opis' in changes:
            new_user.opis = changes['opis']

        if 'avatar' in request.files:
            avatar_file = request.files['avatar']
            if avatar_file and avatar_file.filename != '':
                try:
                    filename = secure_filename(f"{current_user.id}_{int(time.time())}_{avatar_file.filename}")

                    if not os.path.exists(app.config['UPLOAD_FOLDER']):
                        os.makedirs(app.config['UPLOAD_FOLDER'])

                    avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    avatar_file.save(avatar_path)

                    new_user.zdjecie_wskaznik = filename

                    flash(f'Zdjęcie profilowe zostało zaktualizowane: {filename}')
                except Exception as e:
                    logging.error(f"Błąd podczas zapisywania pliku: {str(e)}")
                    flash(f'Wystąpił błąd podczas zapisywania zdjęcia: {str(e)}')
            else:
                logging.debug("Nie wybrano pliku lub nazwa pliku jest pusta")

        try:
            db.session.commit()
            flash('Profil został zaktualizowany pomyślnie.')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Błąd podczas aktualizacji profilu: {str(e)}")
            flash(f'Wystąpił błąd podczas aktualizacji profilu: {str(e)}')

        return redirect(url_for('profile'))

    return redirect(url_for('profile'))




def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        nick = request.form.get('nick')
        mail = request.form.get('mail')
        password = request.form.get('password')
        print(f"nick: {nick}, mail: {mail}, password: {password}")

        if not nick or not mail or not password:
            flash('Wszystkie pola są wymagane.')
            return redirect(url_for('register'))
        if User.query.filter((User.mail == mail) | (User.nick == nick)).first():
            flash('Email lub nick już istnieje.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(
            nick=nick,
            mail=mail,
            password=hashed_password,
            opis="",
            zdjecie_wskaznik='static/basics/profile.png',
            fs_uniquifier=str(uuid.uuid4()),
            active=True
        )
        db.session.add(new_user)
        db.session.commit()

        user_role = Role.query.filter_by(name='user').first()
        if user_role:
            new_user.roles.append(user_role)
            db.session.commit()

        login_user(new_user)
        return redirect(url_for('main'))
    except Exception as e:
        db.session.rollback()
        print(f"Błąd podczas rejestracji: {e}")
        flash('Wystąpił błąd podczas rejestracji.')
        return redirect(url_for('register'))
    try:
        nick = request.form.get('nick')
        mail = request.form.get('mail')
        password = request.form.get('password')
        print(f"nick: {nick}, mail: {mail}, password: {password}")

        if not nick or not mail or not password:
            flash('Wszystkie pola są wymagane.')
            return redirect(url_for('register'))
        if User.query.filter((User.mail == mail) | (User.nick == nick)).first():
            flash('Email lub nick już istnieje.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(
            nick=nick,
            mail=mail,
            password=hashed_password,
            opis="",
            zdjecie_wskaznik='basics/profile.png',  # Set default avatar
            fs_uniquifier=str(uuid.uuid4()),
            active=True
        )
        db.session.add(new_user)
        db.session.commit()

        # Przypisz rolę "user" do nowego użytkownika
        user_role = Role.query.filter_by(name='user').first()
        if user_role:
            new_user.roles.append(user_role)
            db.session.commit()

        login_user(new_user)
        return redirect(url_for('main'))
    except Exception as e:
        db.session.rollback()
        print(f"Błąd podczas rejestracji: {e}")
        flash('Wystąpił błąd podczas rejestracji.')
        return redirect(url_for('register'))







@app.route('/download/<filename>')
def download_file(filename):
    uploads_dir = os.path.join(app.root_path, 'static', 'uploads')
    return send_from_directory(directory=uploads_dir, path=filename, as_attachment=True)




@app.route('/public_post', methods=['POST'])
@login_required
def add_public_post():
    try:
        text = request.form.get('text')
        is_private = request.form.get('is_private') == 'on'
        files = request.files.getlist('files')

        new_post = public_post(text=text, author=current_user, isprivate=is_private)
        db.session.add(new_post)
        db.session.flush()  # To get the id of the new post

        for file in files:
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                file_type = file.content_type
                new_attachment = PostAttachment(post_id=new_post.id, file_name=filename, file_path=file_path, file_type=file_type)
                db.session.add(new_attachment)

        db.session.commit()
        return jsonify({"message": "Post został dodany pomyślnie.", "status": "SUCCESS"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Błąd podczas dodawania posta: {str(e)}")
        return jsonify({"message": "Wystąpił błąd podczas tworzenia posta.", "status": "ERROR"}), 500







@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Create roles
        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(name='user', description='Regular user')
            db.session.add(user_role)

        db.session.commit()

    app.run(host='0.0.0.0', port=5555, debug=True)


    
    
################################################################
# co trzeba zrobić, aby ładnie wyglądało:
# - naprawić aby flask działał z fetch
# - ulepszyć wyglląd main.html
# - dodać ładne przejście fetch z animacjom po zalogowaniu
# - urzyć zwykłych przejść fetchowych w innych zakładkach
# - przywrócić system particle pozbywając się problemu z zapychaniemie pamięci oraz dodać opcje kliknięcia aby zmienić mouseForce na -10
################################################################
# co zrobić aby wszystko działało:
# - dodać sprawdzanie danych w formularzach rejestracji i logowania nick nie może mieć @
# - zrobić wyszukiwarkę po nicku
# - zrobić bazy danych do wszystkich wiadomości które bedą zlinkowane z innymi bazami danych do koemntarzy
# - dodać opcję usuwania wiadomości
# - dodać opcję edycji wiadomości
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
