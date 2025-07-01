# Flask Backend with Admin Content Control and JWT Security
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from .models import *

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY")

# Extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Models
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

class PageContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(50), nullable=False, unique=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.before_first_request
def create_tables():
    db.create_all()
    # seed content if not exists
    default_pages = ['home', 'products', 'about', 'contact', 'careers']
    for page in default_pages:
        if not PageContent.query.filter_by(page=page).first():
            db.session.add(PageContent(page=page, title=f"{page.title()} Page", description=f"Default {page} content."))
    db.session.commit()

# Page routes
@app.route("/<page>")
def get_page(page):
    content = PageContent.query.filter_by(page=page).first()
    if content:
        return jsonify({"title": content.title, "description": content.description})
    return jsonify({"error": "Page not found"}), 404

@app.route("/update/<page>", methods=["PUT"])
@jwt_required()
def update_page(page):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    content = PageContent.query.filter_by(page=page).first()
    if content:
        content.title = data.get("title", content.title)
        content.description = data.get("description", content.description)
        db.session.commit()
        return jsonify({"message": f"{page.title()} page updated."})
    return jsonify({"error": "Page not found"}), 404

# Blog routes
@app.route("/blog")
def get_blogs():
    blogs = Blog.query.order_by(Blog.date_posted.desc()).all()
    return jsonify([{"title": b.title, "content": b.content, "date_posted": b.date_posted} for b in blogs])

@app.route("/blog", methods=["POST"])
@jwt_required()
def add_blog():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Invalid user"}), 401
    data = request.json
    new_blog = Blog(title=data['title'], content=data['content'])
    db.session.add(new_blog)
    db.session.commit()
    return jsonify({"message": "Blog added successfully!"})

# Auth
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 400
    hashed_password = generate_password_hash(data['password'])
    user = User(username=data['username'], password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created successfully"})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=1))
        return jsonify({"message": "Login successful", "access_token": access_token, "user_id": user.id, "is_admin": user.is_admin})
    return jsonify({"error": "Invalid credentials"}), 401

# Chat
@app.route("/chat", methods=["GET"])
def chat():
    messages = Message.query.order_by(Message.timestamp).all()
    return jsonify([
        {"user": User.query.get(m.user_id).username, "message": m.message, "timestamp": m.timestamp} for m in messages
    ])

@app.route("/chat", methods=["POST"])
@jwt_required()
def post_message():
    user_id = get_jwt_identity()
    data = request.json
    msg = Message(user_id=user_id, message=data['message'])
    db.session.add(msg)
    db.session.commit()
    return jsonify({"message": "Message posted"})

# Admin routes
@app.route("/admin/users")
@jwt_required()
def admin_users():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    users = User.query.all()
    return jsonify([{ "id": u.id, "username": u.username, "is_admin": u.is_admin } for u in users])

@app.route("/admin/create", methods=["POST"])
@jwt_required()
def create_admin():
    data = request.json
    if data.get("pin") != "2312":
        return jsonify({"error": "Invalid PIN"}), 403
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "User already exists"}), 400
    hashed_password = generate_password_hash(data['password'])
    new_user = User(username=data['username'], password=hashed_password, is_admin=True)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Admin user created"})

@app.route("/admin/delete", methods=["POST"])
@jwt_required()
def delete_admin():
    data = request.json
    if data.get("pin") != "2312":
        return jsonify({"error": "Invalid PIN"}), 403
    user = User.query.filter_by(username=data['username'], is_admin=True).first()
    if not user:
        return jsonify({"error": "Admin user not found"}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Admin user deleted"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
