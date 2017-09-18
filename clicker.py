import functools

import eventlet
import eventlet.wsgi
from flask import Flask, render_template, request, redirect, session, url_for
from flask_login import current_user, LoginManager, login_required
from flask_login import login_user, logout_user
from flask_socketio import disconnect, SocketIO

from clicker import socket_conn
from clicker import user
from clicker import auth

app = Flask(__name__)
sio = SocketIO(app)
login_manager = LoginManager()
login_manager.init_app(app)
auth = auth.Auth()


@login_manager.user_loader
def load_user(username):
    if auth.user_exists(username):
        return user.User(username)
    return None


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/game')
@login_required
def game():
    return render_template('game.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password').encode()
        if auth.authenticate(username, password):
            if login_user(user.User(username)):
                return redirect(url_for('game'))
        return render_template('login.html',
                               error='Incorrect Username or Password')
    elif current_user.is_authenticated:
        return redirect(url_for('game'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password').encode()
        confirm = request.form.get('confirm').encode()
        result = auth.register(username, password, confirm)
        if result == 'Success':
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error=result)
    return render_template('register.html')


def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped


@sio.on('connect')
@authenticated_only
def connect():
    sock_conn = socket_conn.SockConn(request.sid, current_user.get_id())
    sock_conn.load()
    print('connect: ', request.sid)


@sio.on('click')
@authenticated_only
def click(message):
    sock_conn = socket_conn.SockConn(request.sid)
    sock_conn.click(message)


@sio.on('update')
@authenticated_only
def update():
    sock_conn = socket_conn.SockConn(request.sid)
    return sock_conn.get_update()


@sio.on('upgrade')
@authenticated_only
def upgrade(json):
    sock_conn = socket_conn.SockConn(request.sid)
    sock_conn.upgrade(json)


@sio.on('achievements')
@authenticated_only
def achievements():
    sock_conn = socket_conn.SockConn(request.sid)
    return sock_conn.achievements()


@sio.on('lottery')
@authenticated_only
def lottery(message):
    sock_conn = socket_conn.SockConn(request.sid)
    return sock_conn.lottery(message)


@sio.on('frenzy')
@authenticated_only
def frenzy():
    sock_conn = socket_conn.SockConn(request.sid)
    return sock_conn.frenzy()


if __name__ == "__main__":
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    sio.run(app, port=8000, debug=True)
