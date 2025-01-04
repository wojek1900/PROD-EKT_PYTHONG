import os
import time
import logging
import random
import string
import json
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask_login import current_user 
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, send_file
from flask_security import Security, UserMixin, RoleMixin, SQLAlchemyUserDatastore
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
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


friendships = db.Table('friendships',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

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

    friends = db.relationship(
        'User', 
        secondary=friendships,
        primaryjoin=(friendships.c.user_id == id),
        secondaryjoin=(friendships.c.friend_id == id),
        backref=db.backref('friended_by', lazy='dynamic'),
        lazy='dynamic'
    )

    followers = db.relationship(
        'User', 
        secondary=followers,
        primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        backref=db.backref('following', lazy='dynamic'),
        lazy='dynamic'
    )
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

    def add_friend(self, user):
        if not self.is_friend(user):
            self.friends.append(user)
            user.friends.append(self)

    def remove_friend(self, user):
        if self.is_friend(user):
            self.friends.remove(user)
            user.friends.remove(self)

    def is_friend(self, user):
        return self.friends.filter(friendships.c.friend_id == user.id).count() > 0

    def follow(self, user):
        if not self.is_following(user):
            self.following.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user_id):
        if isinstance(user_id, int):
            return self.following.filter(followers.c.followed_id == user_id).count() > 0
        elif isinstance(user_id, User):
            return self.following.filter(followers.c.followed_id == user_id.id).count() > 0
        else:
            return False

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.fs_uniquifier:
            self.fs_uniquifier = str(uuid.uuid4())
        if not self.zdjecie_wskaznik:
            self.zdjecie_wskaznik = 'basics/profile.png'





class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    zdjecie_wskaznik = db.Column(db.String(255), nullable=False)
    join_code = db.Column(db.String(6), unique=True, nullable=False)
    group_creator = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', secondary='group_users', backref=db.backref('groups', lazy='dynamic'))
    messages = db.relationship('GroupMessage', backref='group', lazy='dynamic', cascade="all, delete-orphan")
    reactions = db.relationship('GroupReaction', backref='group', lazy='dynamic', cascade="all, delete-orphan")

    def generate_join_code(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))

    def __init__(self, **kwargs):
        super(Group, self).__init__(**kwargs)
        if not self.join_code:
            self.join_code = self.generate_join_code()

class GroupUser(db.Model):
    __tablename__ = 'group_users'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    admin = db.Column(db.Boolean, default=False)

    group = db.relationship('Group', backref=db.backref('group_users', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('user_groups', lazy='dynamic'))

    def make_admin(self):
        self.admin = True

    def remove_admin(self):
        self.admin = False
        
        
class GroupMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', backref=db.backref('group_messages', lazy='dynamic'))
    attachments = db.relationship('GroupMessageAttachment', back_populates='message', cascade="all, delete-orphan")
    reactions = db.relationship('GroupReaction', back_populates='message', lazy='dynamic', cascade="all, delete-orphan")

class GroupReaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('group_message.id'), nullable=False)
    reaction_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    message = db.relationship('GroupMessage', back_populates='reactions')
    user = db.relationship('User', backref=db.backref('group_reactions', lazy='dynamic'))
    

class GroupMessageAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(100), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('group_message.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    message = db.relationship('GroupMessage', back_populates='attachments')




class PrivateMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    attachments = db.relationship('PrivateMessageAttachment', back_populates='private_message', lazy='dynamic')

    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy='dynamic'))
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref=db.backref('received_messages', lazy='dynamic'))
    reactions = db.relationship('PrivateMessageReaction', back_populates='private_message', cascade="all, delete-orphan")



class PrivateMessageAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('private_message.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(1024), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    private_message = db.relationship('PrivateMessage', back_populates='attachments')



class PrivateMessageReaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('private_message.id'), nullable=False)
    reaction_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', backref=db.backref('private_message_reactions', lazy='dynamic'))
    private_message = db.relationship('PrivateMessage', back_populates='reactions')




class PostAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('public_post.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(1024), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False) 
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    post = db.relationship('public_post', back_populates='post_attachments')



class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('public_post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)
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
    tags = db.relationship('Tag', secondary='post_tags', backref=db.backref('posts', lazy='dynamic'))

    def add_tag(self, tag_name):
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag_name):
        tag = Tag.query.filter_by(name=tag_name).first()
        if tag and tag in self.tags:
            self.tags.remove(tag)

    def get_tags(self):
        return [tag.name for tag in self.tags]

    def __init__(self, **kwargs):
        super(public_post, self).__init__(**kwargs)
        if not self.fs_uniquifier:
            self.fs_uniquifier = str(uuid.uuid4())


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
    search_query = request.args.get('search_query', '')
    search_type = request.args.get('search_type', 'post_text')

    posts_query = public_post.query

    if search_query:
        if search_type == 'tag':
            posts_query = posts_query.filter(public_post.tags.any(Tag.name.ilike(f'%{search_query}%')))
        else:
            posts_query = posts_query.filter(public_post.text.ilike(f'%{search_query}%'))

    posts = posts_query.order_by(public_post.created_at.desc()).all()
    return render_template('main.html', user=current_user, posts=posts, search_query=search_query, search_type=search_type)




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
        tags = request.form.get('tags', '').split(',')

        new_post = public_post(text=text, author=current_user, isprivate=is_private, comments_allowed=no_comments)

        for tag in tags:
            tag = tag.strip()
            if tag:
                new_post.add_tag(tag)


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
        post.edited_at = datetime.utcnow().now()
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
            created_at=datetime.utcnow().now(),
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






@app.route('/following.html')
@login_required
def following():
    return render_template('following.html',user=current_user, posts=public_post.query.filter_by(isprivate=False).order_by(public_post.created_at.desc()).all())




@app.route('/search.html', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        users = User.query.filter(User.nick.ilike(f'%{search_query}%')).all()
        return render_template('search.html', users=users, search_performed=True)
    return render_template('search.html')

@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    user = User.query.get_or_404(user_id)
    if current_user.is_following(user):
        current_user.unfollow(user)
        db.session.commit()
        flash('Przestałeś obserwować użytkownika.', 'success')
    else:
        current_user.follow(user)
        db.session.commit()
        flash('Zacząłeś obserwować użytkownika.', 'success')
    return redirect(url_for('user_profile', user_id=user_id))





@app.route('/add_friend/<int:user_id>', methods=['POST'])
@login_required
def add_friend(user_id):
    user = User.query.get_or_404(user_id)
    if current_user.is_friend(user):
        current_user.remove_friend(user)
        db.session.commit()
        flash('Usunięto z listy przyjaciół.', 'success')
    else:
        current_user.add_friend(user)
        db.session.commit()
        flash('Dodano do listy przyjaciół.', 'success')
    return redirect(url_for('user_profile', user_id=user_id))







@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))







@app.route('/private.html', methods=['GET']) 
@login_required
def private():
    user_groups = current_user.groups.all()
    user_friends = current_user.friends.all()
    return render_template('private.html', groups=user_groups, friends=user_friends)





@app.route('/private_chat/<int:friend_id>')
@login_required
def private_chat(friend_id):
    friend = User.query.get_or_404(friend_id)
    messages = PrivateMessage.query.filter(
        ((PrivateMessage.sender_id == current_user.id) & (PrivateMessage.recipient_id == friend_id)) |
        ((PrivateMessage.sender_id == friend_id) & (PrivateMessage.recipient_id == current_user.id))
    ).order_by(PrivateMessage.created_at).all()
    return render_template('private_chat.html', friend=friend, messages=messages)




@app.route('/send_private_message/<int:recipient_id>', methods=['POST'])
@login_required
def send_private_message(recipient_id):
    try:
        message_text = request.form.get('message')
        files = request.files.getlist('files')
        if not message_text and not files:
            return jsonify({"status": "error", "message": "No message or files provided"}), 400

        new_message = PrivateMessage(sender_id=current_user.id, recipient_id=recipient_id, message=message_text)
        db.session.add(new_message)
        db.session.flush() 
        for file in files:
            if file:
                original_filename = secure_filename(file.filename)
                file_extension = os.path.splitext(original_filename)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)

                attachment = PrivateMessageAttachment(
                    message_id=new_message.id,
                    file_name=unique_filename,
                    original_filename=original_filename,
                    file_path=file_path,
                    file_type=file.content_type
                )
                db.session.add(attachment)
        db.session.commit()
        return jsonify({
            "status": "OK",
            "message": new_message.message,
            "attachments": [
                {
                    "file_name": attachment.file_name,
                    "original_filename": attachment.original_filename,
                    "file_path": attachment.file_path,
                    "file_type": attachment.file_type
                } for attachment in new_message.attachments
            ]
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in send_private_message: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500




@app.route('/download_private_file/<int:attachment_id>')
@login_required
def download_private_file(attachment_id):
    attachment = PostAttachment.query.get_or_404(attachment_id)
    uploads_dir = os.path.join(app.root_path, 'static', 'uploads')
    file_path = os.path.join(uploads_dir, attachment.file_name)

    return send_file(
        file_path, 
        as_attachment=True, 
        download_name=attachment.original_filename,
        mimetype=attachment.file_type
    )




@app.route('/react_to_message', methods=['POST'])
@login_required
def react_to_message():
    message_id = request.form.get('message_id')
    reaction_type = request.form.get('reaction_type')

    print(f"Received request: message_id={message_id}, reaction_type={reaction_type}")  # Debug log

    if message_id and reaction_type:
        existing_reaction = PrivateMessageReaction.query.filter_by(
            message_id=message_id, user_id=current_user.id
        ).first()

        try:
            if existing_reaction:
                if existing_reaction.reaction_type == reaction_type:
                    print(f"Deleting existing reaction: {existing_reaction}")  # Debug log
                    db.session.delete(existing_reaction)
                else:
                    print(f"Updating existing reaction: {existing_reaction} to {reaction_type}")  # Debug log
                    existing_reaction.reaction_type = reaction_type
            else:
                new_reaction = PrivateMessageReaction(
                    message_id=message_id,
                    user_id=current_user.id,
                    reaction_type=reaction_type
                )
                print(f"Adding new reaction: {new_reaction}")  # Debug log
                db.session.add(new_reaction)

            db.session.commit()
            print("Database session committed successfully")  # Debug log
            return jsonify({'status': 'success', 'message': 'Reaction updated'})
        except Exception as e:
            db.session.rollback()
            print(f"Error occurred: {str(e)}")  # Debug log
            return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'})

    print("Invalid data received")  # Debug log
    return jsonify({'status': 'error', 'message': 'Invalid data'})




@app.route('/delete_private_message', methods=['POST'])
@login_required
def delete_private_message():
    message_id = request.form.get('message_id')
    message = PrivateMessage.query.get_or_404(message_id)

    if message.sender_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    for attachment in message.attachments:
        os.remove(attachment.file_path)
        db.session.delete(attachment)

    db.session.delete(message)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Message deleted'})




@app.route('/edit_private_message/<int:message_id>', methods=['POST'])
@login_required
def edit_private_message(message_id):
    message = PrivateMessage.query.get_or_404(message_id)
    if message.sender_id != current_user.id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    message.message = request.form['message']

    # Handle existing attachments
    existing_attachment_ids = request.form.getlist('existing_attachments[]')
    print(f"Existing attachments: {existing_attachment_ids}")
    attachments_to_delete = []
    for attachment in message.attachments:
        if str(attachment.id) not in existing_attachment_ids:
            attachments_to_delete.append(attachment)
    print(f"Attachments to delete: {attachments_to_delete}")
    # Handle new files
    new_files = request.files.getlist('new_files[]')
    new_attachments = []
    for file in new_files:
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            new_attachment = PrivateMessageAttachment(
                file_name=filename,
                original_filename=file.filename,
                file_path=file_path,
                file_type=file.content_type,
                message_id=message.id,
                created_at=datetime.now()
            )
            new_attachments.append(new_attachment)

    # Update database in a single transaction
    try:
        for attachment in attachments_to_delete:
            db.session.delete(attachment)
        for new_attachment in new_attachments:
            db.session.add(new_attachment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

    # Prepare response data
    attachments_data = [{
    'id': att.id,
    'type': 'img' if att.file_type.startswith('image/') else
            'video' if att.file_type.startswith('video/') else
            'audio' if att.file_type.startswith('audio/') else 'file',
    'src': url_for('static', filename=f'uploads/{att.file_name}'),
    'name': att.original_filename  # Dodaj nazwę oryginalnego pliku
    } for att in message.attachments]

    return jsonify({
        "status": "OK",
        "message": "Message updated successfully",
        "attachments": attachments_data
    })





@app.route('/get_new_messages/<int:friend_id>')
@login_required
def get_new_messages(friend_id):
    messages = PrivateMessage.query.filter(
        ((PrivateMessage.sender_id == current_user.id) & (PrivateMessage.recipient_id == friend_id)) |
        ((PrivateMessage.sender_id == friend_id) & (PrivateMessage.recipient_id == current_user.id))
    ).order_by(PrivateMessage.created_at).all()

    messages_data = []
    for msg in messages:
        reactions = {}
        for reaction in msg.reactions:
            if reaction.reaction_type in reactions:
                reactions[reaction.reaction_type] += 1
            else:
                reactions[reaction.reaction_type] = 1

        user_reaction = next((r.reaction_type for r in msg.reactions if r.user_id == current_user.id), None)
        reactions['user_reaction'] = user_reaction

        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'message': msg.message,
            'created_at': msg.created_at.isoformat(),
            'reactions': reactions,
            "attachments": [
                {
                    "id": attachment.id,
                    "file_name": attachment.file_name,
                    "original_filename": attachment.original_filename,
                    "file_path": attachment.file_path,
                    "file_type": attachment.file_type
                } for attachment in msg.attachments
            ]
        })

    return jsonify(messages_data)




@app.route('/group_chat/<int:group_id>')
@login_required
def group_chat(group_id):
    group = Group.query.get_or_404(group_id)
    if current_user not in group.users:
        flash('You are not a member of this group.', 'error')
        return redirect(url_for('main'))
    return render_template('group_chat.html', group=group, messages=group.messages)




@app.route('/create_group', methods=['POST'])
@login_required
def create_group():
    name = request.form.get('name')
    if not name:
        return jsonify({'status': 'error', 'message': 'Group name is required'}), 400

    new_group = Group(name=name, zdjecie_wskaznik='basics/group.png', group_creator=current_user.id)
    new_group.users.append(current_user)
    db.session.add(new_group)
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Group created successfully',
            'group_id': new_group.id,
            'join_code': new_group.join_code
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500




@app.route('/join_group', methods=['POST'])
@login_required
def join_group():
    join_code = request.form.get('join_code')
    if not join_code:
        return jsonify({'status': 'error', 'message': 'Join code is required'}), 400

    group = Group.query.filter_by(join_code=join_code).first()
    if not group:
        return jsonify({'status': 'error', 'message': 'Invalid join code'}), 404

    if current_user in group.users:
        return jsonify({'status': 'error', 'message': 'You are already a member of this group'}), 400

    if group.group_creator == current_user.id:
        return jsonify({'status': 'error', 'message': 'You cannot join your own group'}), 400

    group.users.append(current_user)
    try:
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Joined group successfully', 'group_id': group.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500




@app.route('/send_group_message/<int:group_id>', methods=['POST'])
@login_required
def send_group_message(group_id):
    try:
        group = Group.query.get_or_404(group_id)
        if current_user not in group.users:
            return jsonify({"status": "error", "message": "You are not a member of this group"}), 403
        message_text = request.form.get('message')
        files = request.files.getlist('files')
        if not message_text and not files:
            return jsonify({"status": "error", "message": "No message or files provided"}), 400

        new_message = GroupMessage(user_id=current_user.id, group_id=group_id, message=message_text)
        db.session.add(new_message)
        db.session.flush() 

        attachments = []
        for file in files:
            if file:
                original_filename = secure_filename(file.filename)
                file_extension = os.path.splitext(original_filename)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)

                attachment = GroupMessageAttachment(
                    message_id=new_message.id,
                    file_name=unique_filename,
                    original_filename=original_filename,
                    file_path=file_path,
                    file_type=file.content_type
                )
                db.session.add(attachment)
                attachments.append({
                    "file_name": unique_filename,
                    "original_filename": original_filename,
                    "file_path": file_path,
                    "file_type": file.content_type
                })
        db.session.commit()
        return jsonify({
            "status": "OK",
            "message": new_message.message,
            "message_id": new_message.id,
            "sender_id": current_user.id,
            "sender_nick": current_user.nick,
            "created_at": new_message.created_at.isoformat(),
            "attachments": attachments
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in send_group_message: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500





@app.route('/leave_group', methods=['POST'])
@login_required
def leave_group():
    group_id = request.form.get('group_id')
    if not group_id:
        return jsonify({'status': 'error', 'message': 'Group ID is required'}), 400

    group = Group.query.get(group_id)
    if not group:
        return jsonify({'status': 'error', 'message': 'Invalid group'}), 404

    if current_user not in group.users:
        return jsonify({'status': 'error', 'message': 'You are not a member of this group'}), 400

    if group.group_creator == current_user.id:
        return jsonify({'status': 'error', 'message': 'Group creator cannot leave the group'}), 400

    group.users.remove(current_user)
    try:
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Left group successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500





@app.route('/get_group_messages/<int:group_id>')
@login_required
def get_group_messages(group_id):
    group = Group.query.get_or_404(group_id)
    if current_user not in group.users:
        return jsonify({'status': 'error', 'message': 'You are not a member of this group'}), 403

    messages = GroupMessage.query.filter_by(group_id=group_id).order_by(GroupMessage.created_at).all()

    messages_data = []
    for msg in messages:
        reactions = {}
        for reaction in msg.reactions:
            if reaction.reaction_type in reactions:
                reactions[reaction.reaction_type] += 1
            else:
                reactions[reaction.reaction_type] = 1

        user_reaction = next((r.reaction_type for r in msg.reactions if r.user_id == current_user.id), None)
        reactions['user_reaction'] = user_reaction

        messages_data.append({
            'id': msg.id,
            'sender_id': msg.user_id,
            'sender_nick': msg.user.nick,
            'message': msg.message,
            'created_at': msg.created_at.isoformat(),
            'reactions': reactions,
            "attachments": [
                {
                    "id": attachment.id,
                    "file_name": attachment.file_name,
                    "original_filename": attachment.original_filename,
                    "file_path": attachment.file_path,
                    "file_type": attachment.file_type
                } for attachment in msg.attachments
            ]
        })

    return jsonify({'status': 'success', 'messages': messages_data})






@app.route('/react_to_group_message', methods=['POST'])
@login_required
def react_to_group_message():
    message_id = request.form.get('message_id')
    reaction_type = request.form.get('reaction_type')

    print(f"Received request: message_id={message_id}, reaction_type={reaction_type}")  # Debug log

    if message_id and reaction_type:
        message = GroupMessage.query.get_or_404(message_id)
        if current_user not in message.group.users:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        existing_reaction = GroupReaction.query.filter_by(
            message_id=message_id, user_id=current_user.id
        ).first()

        try:
            if existing_reaction:
                if existing_reaction.reaction_type == reaction_type:
                    print(f"Deleting existing reaction: {existing_reaction}")  # Debug log
                    db.session.delete(existing_reaction)
                else:
                    print(f"Updating existing reaction: {existing_reaction} to {reaction_type}")  # Debug log
                    existing_reaction.reaction_type = reaction_type
            else:
                new_reaction = GroupReaction(
                    group_id=message.group_id,  
                    message_id=message_id,
                    user_id=current_user.id,
                    reaction_type=reaction_type
                )
                print(f"Adding new reaction: {new_reaction}")  # Debug log
                db.session.add(new_reaction)

            db.session.commit()
            print("Database session committed successfully")  # Debug log
            return jsonify({'status': 'success', 'message': 'Reaction updated'})
        except Exception as e:
            db.session.rollback()
            print(f"Error occurred: {str(e)}")  # Debug log
            return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'})

    print("Invalid data received")  # Debug log
    return jsonify({'status': 'error', 'message': 'Invalid data'})

@app.route('/delete_group_message', methods=['POST'])
@login_required
def delete_group_message():
    message_id = request.form.get('message_id')
    message = GroupMessage.query.get_or_404(message_id)

    if message.user_id != current_user.id and current_user.id != message.group.group_creator:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    for attachment in message.attachments:
        os.remove(attachment.file_path)
        db.session.delete(attachment)

    db.session.delete(message)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Message deleted'})

@app.route('/edit_group_message/<int:message_id>', methods=['POST'])
@login_required
def edit_group_message(message_id):
    message = GroupMessage.query.get_or_404(message_id)
    if message.user_id != current_user.id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    message.message = request.form['message']

    # Handle existing attachments
    existing_attachment_ids = request.form.getlist('existing_attachments[]')
    print(f"Existing attachments: {existing_attachment_ids}")
    attachments_to_delete = []
    for attachment in message.attachments:
        if str(attachment.id) not in existing_attachment_ids:
            attachments_to_delete.append(attachment)
    print(f"Attachments to delete: {attachments_to_delete}")

    # Handle new files
    new_files = request.files.getlist('new_files[]')
    new_attachments = []
    for file in new_files:
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            new_attachment = GroupMessageAttachment(
                file_name=filename,
                original_filename=file.filename,
                file_path=file_path,
                file_type=file.content_type,
                message_id=message.id,
                created_at=datetime.now()
            )
            new_attachments.append(new_attachment)

    # Update database in a single transaction
    try:
        for attachment in attachments_to_delete:
            db.session.delete(attachment)
        for new_attachment in new_attachments:
            db.session.add(new_attachment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

    # Prepare response data
    attachments_data = [{
        'id': att.id,
        'type': 'img' if att.file_type.startswith('image/') else
                'video' if att.file_type.startswith('video/') else
                'audio' if att.file_type.startswith('audio/') else 'file',
        'src': url_for('static', filename=f'uploads/{att.file_name}'),
        'name': att.original_filename
    } for att in message.attachments]

    return jsonify({
        "status": "OK",
        "message": "Message updated successfully",
        "attachments": attachments_data
    })

@app.route('/download_group_file/<int:attachment_id>')
@login_required
def download_group_file(attachment_id):
    attachment = GroupMessageAttachment.query.get_or_404(attachment_id)
    if current_user not in attachment.message.group.users:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    uploads_dir = os.path.join(app.root_path, 'static', 'uploads')
    file_path = os.path.join(uploads_dir, attachment.file_name)

    return send_file(
        file_path, 
        as_attachment=True,
        download_name=attachment.original_filename,
        mimetype=attachment.file_type
    )









if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(name='user', description='Regular user')
            db.session.add(user_role)

        db.session.commit()
        
        if not User.query.filter_by(nick='test').first():
            user = User(nick='test', password=generate_password_hash('test'), mail='test@test.com')
            db.session.add(user)
            user1 = User(nick='test1', password=generate_password_hash('test1'), mail='test1@test.com')
            db.session.add(user1)
            
            db.session.commit()

    app.run(host='0.0.0.0', port=5555, debug=True)


# co jak najszybciej
# usuwanie grup przez właściciela grupy
# dodanie adminów do grup
# dodanie możliwości usuwania wiadomości w grupach dla adminów
# dodać opis grupy i jej członków
# poprawnie wyświetlanie we wiadomosciach prywatnych i grupach avatarów i odnośników do ich profilów
# właściciel grupy może usuwać i dodawać adminów w grupie
# dodanie przycisku dla twurcy i adminów grupy kod dostępu
# formatowanie tekstu w postach wiadomościach komentarzach i opisach
# dodać system przyjmowania znajomych
# dodać system ignorowania osób




# co w następnym tygodniu spróbuje zrobić
# usuwanie komentarzy z postów
# naprawić robienie postów i dodanie plików a potem ich usuwanie 
# naprawić przekierowanie na strony czasem działa czasem nei zalezy gdzie się jest wystarczy poprawić odsyłanie na odpowiednie
# naprawić nie ma opcji edycji usuwania postów dodawani komentarzy itd w profilu w stronie postu 
# naprawić brak wyświetlania poprawnej liczby komentarzy kiedy się ich nie odsłoni bo zawsze jest 0 na początku
# naprawić to żeby admin nie widział przycisku do edycji 
# dodać powiadomienia









################################################################
# co trzeba zrobić, aby ładnie wyglądało:
# - w sumie i tak zmienić cały design
# - naprawić aby flask działał z fetch
# - ulepszyć wyglląd main.html
# - dodać ładne przejście fetch z animacjom po zalogowaniu
# - urzyć zwykłych przejść fetchowych w innych zakładkach
# - przywrócić system particle dodać opcje kliknięcia aby zmienić mouseForce na -10
################################################################
# - powiadomienia o wszystkim
# - zlinkowanie AI jak llama czy qwen do analizy komentarzy i danych
# - jak wszystko się uda sprubować urzywając tensorflowa wybierać trafne treści dla urzytkownika
################################################################

