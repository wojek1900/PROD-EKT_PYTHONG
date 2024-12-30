import os
import time
import logging
import datetime
import json
from werkzeug.utils import secure_filename
from flask_login import current_user 
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, send_file
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



user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
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
    zdjecie_wskaznik = db.Column(db.String(255), nullable=False)
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    active = db.Column(db.Boolean(), default=True)
    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))

    def make_admin(self):
        self.roles.append(Role.query.filter_by(name='admin').first())
    def remove_admin(self):
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role in self.roles:
            self.roles.remove(admin_role)  
    def has_role(self, role_name):
        if role_name == 'admin':
            admin_role = Role.query.filter_by(name='admin').first()
            return admin_role in self.roles
        return False

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
    original_filename = db.Column(db.String(255), nullable=False) 
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
    post_comments = db.relationship('public_comment', back_populates='post')
    post_reactions = db.relationship('public_reaction', back_populates='post')
    tags = db.relationship('public_tag', secondary='post_tags', backref=db.backref('posts', lazy='dynamic'))
    edited_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    is_edited = db.Column(db.Boolean(), default=False)
    comments_allowed = db.Column(db.Boolean, default=True)
    
    def __init__(self, **kwargs):
        super(public_post, self).__init__(**kwargs)
        if not self.fs_uniquifier:
            self.fs_uniquifier = str(uuid.uuid4())

class public_tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('public_post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('public_tag.id'), primary_key=True)
)

class public_comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(4096), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='comments')
    post_id = db.Column(db.Integer, db.ForeignKey('public_post.id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    edited_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    is_edited = db.Column(db.Boolean(), default=False)

    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    post = db.relationship('public_post', back_populates='post_comments')
    
    
class public_reaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('public_post.id'))
    reaction_type = db.Column(db.String(50), nullable=False)

    user = db.relationship('User', backref=db.backref('reactions', lazy=True))
    post = db.relationship('public_post', back_populates='post_reactions')

    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='user_post_reaction_uc'),)

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


@app.route('/change_profile', methods=['POST'])
@login_required
def change_profile():
    try:
        nick = request.form.get('nick')
        opis = request.form.get('opis')
        avatar = request.files.get('avatar')

        if nick:
            current_user.nick = nick
        if opis:
            current_user.opis = opis

        if avatar:
            original_filename = secure_filename(avatar.filename)
            file_extension = os.path.splitext(original_filename)[1]
            unique_filename = f"avatar_{uuid.uuid4()}{file_extension}"

            avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            avatar.save(avatar_path)

            current_user.zdjecie_wskaznik = unique_filename

        db.session.commit()
        flash('Profil został zaktualizowany pomyślnie.')
        return redirect(url_for('profile'))
    except Exception as e:
        db.session.rollback()
        flash(f'Wystąpił błąd podczas aktualizacji profilu: {str(e)}')
        return redirect(url_for('profile'))



@app.route('/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    admin_role = Role.query.filter_by(name='admin').first()

    if not admin_role:
        #add admin role if it doesn't exist
        admin_role = Role(name='admin')
        db.session.add(admin_role)

    if admin_role in user.roles:
        user.roles.remove(admin_role)
        message = f"Użytkownik {user.nick} nie jest już administratorem."
    else:
        user.roles.append(admin_role)
        message = f"Użytkownik {user.nick} został mianowany administratorem."

    try:
        db.session.commit()
        return jsonify({"status": "OK", "message": message}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "ERROR", "message": str(e)}), 500
    
    


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
        
        # Sprawdzenie, czy nick zawiera znak "@"
        if '@' in nick:
            flash('Nick nie może zawierać znaku "@".')
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
            zdjecie_wskaznik='basics/profile.png', 
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









@app.route('/download/<int:attachment_id>')
def download_file(attachment_id):
    attachment = PostAttachment.query.get_or_404(attachment_id)
    uploads_dir = os.path.join(app.root_path, 'static', 'uploads')
    file_path = os.path.join(uploads_dir, attachment.file_name)

    return send_file(
        file_path, 
        as_attachment=True, 
        download_name=attachment.original_filename,
        mimetype=attachment.file_type
    )






@app.route('/public_post', methods=['POST'])
@login_required
def add_public_post():
    try:
        text = request.form.get('text')
        is_private = request.form.get('is_private') == 'on'
        no_comments = request.form.get('no_comments') == 'on'
        files = request.files.getlist('files')

        new_post = public_post(text=text, author=current_user, isprivate=is_private, comments_allowed=no_comments)
        db.session.add(new_post)
        db.session.flush() 

        for file in files:
            if file:
                original_filename = secure_filename(file.filename)
                file_extension = os.path.splitext(original_filename)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"

                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)

                file_type = file.content_type
                new_attachment = PostAttachment(
                    post_id=new_post.id, 
                    file_name=unique_filename, 
                    original_filename=original_filename,  
                    file_path=file_path, 
                    file_type=file_type
                )
                db.session.add(new_attachment)

        db.session.commit()
        return jsonify({"message": "Post został dodany pomyślnie.", "status": "SUCCESS"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Błąd podczas dodawania posta: {str(e)}")
        return jsonify({"message": "Wystąpił błąd podczas tworzenia posta.", "status": "ERROR"}), 500



REACTION_TYPES = ['like', 'love', 'haha', 'wow', 'sad']

@app.route('/add_reaction/<int:post_id>/<string:reaction_type>', methods=['POST'])
@login_required
def add_reaction(post_id, reaction_type):
    
    
    
    if reaction_type not in REACTION_TYPES:
        return jsonify({'error': 'Invalid reaction type'}), 400

    existing_reaction = public_reaction.query.filter_by(user_id=current_user.id, post_id=post_id).first()

    if existing_reaction:
        if existing_reaction.reaction_type == reaction_type:
            db.session.delete(existing_reaction)
            db.session.commit()
            return jsonify({'message': 'Reaction removed', 'action': 'removed'})
        else:
            existing_reaction.reaction_type = reaction_type
            db.session.commit()
            return jsonify({'message': 'Reaction updated', 'action': 'updated'})
    else:
        new_reaction = public_reaction(user_id=current_user.id, post_id=post_id, reaction_type=reaction_type)
        db.session.add(new_reaction)
        db.session.commit()
        return jsonify({'message': 'Reaction added', 'action': 'added'})

@app.route('/get_reactions/<int:post_id>', methods=['GET'])
def get_reactions(post_id):
    reactions = public_reaction.query.filter_by(post_id=post_id).all()
    reaction_counts = {reaction_type: 0 for reaction_type in REACTION_TYPES}
    
    for reaction in reactions:
        reaction_counts[reaction.reaction_type] += 1
    
    return jsonify(reaction_counts)





@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = public_post.query.get_or_404(post_id)
    try:
        for attachment in post.post_attachments:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], attachment.file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.delete(attachment)
        
        db.session.delete(post)
        db.session.commit()
        return jsonify({"status": "OK", "message": "Post został pomyślnie usunięty."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "ERROR", "message": f"Wystąpił błąd podczas usuwania posta: {str(e)}"}), 500    
    




@app.route('/edit_post/<int:post_id>', methods=['POST'])
@login_required
def edit_post(post_id):
    post = public_post.query.get_or_404(post_id)
    if post.author != current_user:
        return jsonify({"status": "ERROR", "message": "Nie masz uprawnień do edycji tego posta."}), 403

    try:
        new_text = request.form.get('text', '').strip()
        current_attachments = json.loads(request.form.get('attachments', '[]'))
        new_files = request.files.getlist('new_files')

        if not new_text and not current_attachments and not new_files:
            for attachment in post.post_attachments:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], attachment.file_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                db.session.delete(attachment)

            db.session.delete(post)
            db.session.commit()
            return jsonify({"status": "OK", "message": "Post został usunięty, ponieważ był pusty.", "action": "deleted"}), 200

        post.text = new_text

        current_attachment_ids = [att['id'] for att in current_attachments]
        existing_attachments = {str(att.id): att for att in post.post_attachments}

        for att_id, attachment in existing_attachments.items():
            if att_id not in current_attachment_ids:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], attachment.file_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                db.session.delete(attachment)

        for file in new_files:
            if file and file.filename:
                original_filename = secure_filename(file.filename)
                file_extension = os.path.splitext(original_filename)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"

                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)

                new_attachment = PostAttachment(
                    post_id=post.id, 
                    file_name=unique_filename, 
                    original_filename=original_filename,
                    file_path=file_path, 
                    file_type=file.content_type
                )
                db.session.add(new_attachment)

        post.is_edited = True
        post.edited_at = datetime.datetime.now()
        db.session.commit()

        updated_attachments = [{"id": att.id, "filename": att.original_filename, "type": att.file_type} for att in post.post_attachments]
        
        return jsonify({
            "status": "OK", 
            "message": "Post został zaktualizowany.", 
            "attachments": updated_attachments,
            "is_edited": post.is_edited
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "ERROR", 
            "message": f"Wystąpił błąd podczas aktualizacji posta: {str(e)}"
        }), 500





@app.route('/post/<int:post_id>')
@login_required
def view_post(post_id):
    post = public_post.query.get_or_404(post_id)
    return render_template('post.html', post=post)





@app.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    try:
        comment_text = request.form.get('comment-text')
        if not comment_text:
            print(comment_text)
            return jsonify({"status": "ERROR", "message": "Komentarz nie może być pusty."}), 400

        new_comment = public_comment(
            text=comment_text,
            user_id=current_user.id, 
            post_id=post_id,
            created_at=datetime.datetime.now(),
            user=current_user
        )
        db.session.add(new_comment)
        db.session.commit()

        return jsonify({"status": "OK", "message": "Komentarz został dodany."}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Błąd podczas dodawania komentarza: {str(e)}")
        return jsonify({"status": "ERROR", "message": "Wystąpił błąd podczas dodawania komentarza."}), 500


@app.route('/download_avatar/<int:user_id>')
@login_required
def download_avatar(user_id):
    user = User.query.get_or_404(user_id)
    if user.zdjecie_wskaznik and user.zdjecie_wskaznik != "basics/profile.png":
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], user.zdjecie_wskaznik)
        return send_file(file_path, as_attachment=True)
    else:
        return send_file("static/basics/profile.png", as_attachment=True)



@app.route('/user/<int:user_id>')
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    posts = public_post.query.filter_by(author=user).order_by(public_post.created_at.desc()).all()
    return render_template('user_profile.html', user=user, posts=posts)   
    
    
@app.route('/search.html', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        users = User.query.filter(User.nick.ilike(f'%{search_query}%')).all()
        return render_template('search.html', users=users, search_performed=True)
    return render_template('search.html')
  

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(name='user', description='Regular user')
            db.session.add(user_role)

        db.session.commit()

    app.run(host='0.0.0.0', port=5555, debug=True)


    

# poprawić profil urzytkownika rzeby tam też była opcja dodania komentarza i usunięcia oraz zmienienia

################################################################
# co trzeba zrobić, aby ładnie wyglądało:
# - naprawić aby flask działał z fetch
# - ulepszyć wyglląd main.html
# - dodać ładne przejście fetch z animacjom po zalogowaniu
# - urzyć zwykłych przejść fetchowych w innych zakładkach
# - przywrócić system particle pozbywając się problemu z zapychaniemie pamięci oraz dodać opcje kliknięcia aby zmienić mouseForce na -10
################################################################
# co zrobić aby wszystko działało:
# - dodać opcję robienia grup
# - dodać opcję dołączenia do grup
# - dodać opcję usuwania z grup
# - dodać opcje pisania wiadomości do urzytkowników w grupach i prywatnych
# - powiadomienia o nowych wiadomościach
# - zlinkowanie AI jak llama czy qwen do analizy komentarzy i danych
# - zrobienie wykresów z danych postów
# - zrobienie wyszukiwarki po tagach
# - jak wszystko się uda sprubować urzywając tensorflowa wybierać trafne treści dla urzytkownika
###
