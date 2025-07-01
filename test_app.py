import pytest
from app import app, db, User, PageContent, Blog, Message
from flask_jwt_extended import create_access_token
import os
from sqlalchemy_utils import create_database, database_exists, drop_database

TEST_DB_URL = os.environ.get('TEST_DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/test_db')

@pytest.fixture(scope='session')
def setup_postgres():
    # Drop and create the test database
    if database_exists(TEST_DB_URL):
        drop_database(TEST_DB_URL)
    create_database(TEST_DB_URL)
    yield
    drop_database(TEST_DB_URL)

@pytest.fixture
def client(setup_postgres):
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DB_URL
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create a test user
            user = User(username='testuser', password='testpass')
            db.session.add(user)
            db.session.commit()
        yield client
        with app.app_context():
            db.drop_all()


def test_signup_and_login(client):
    # Signup
    resp = client.post('/signup', json={'username': 'pytest', 'password': 'pytestpass'})
    assert resp.status_code == 200
    # Login
    resp = client.post('/login', json={'username': 'pytest', 'password': 'pytestpass'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'access_token' in data


def test_get_page(client):
    resp = client.get('/home')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'title' in data and 'description' in data


def test_blog_crud(client):
    # Signup and login
    client.post('/signup', json={'username': 'blogger', 'password': 'blogpass'})
    login_resp = client.post('/login', json={'username': 'blogger', 'password': 'blogpass'})
    token = login_resp.get_json()['access_token']
    # Add blog
    resp = client.post('/blog', json={'title': 'Test Blog', 'content': 'Blog content'}, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    # Get blogs
    resp = client.get('/blog')
    assert resp.status_code == 200
    blogs = resp.get_json()
    assert isinstance(blogs, list)


def test_chat(client):
    # Signup and login
    client.post('/signup', json={'username': 'chatter', 'password': 'chatpass'})
    login_resp = client.post('/login', json={'username': 'chatter', 'password': 'chatpass'})
    token = login_resp.get_json()['access_token']
    # Post message
    resp = client.post('/chat', json={'message': 'Hello!'}, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    # Get messages
    resp = client.get('/chat')
    assert resp.status_code == 200
    messages = resp.get_json()
    assert isinstance(messages, list) 