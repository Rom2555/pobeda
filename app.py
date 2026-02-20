import sqlite3
from flask import Flask, jsonify, g, send_from_directory, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
DATABASE = 'users.db'


def get_db():
    """Get database connection."""
    db = getattr(g, '_database', None)
    if db is None:
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    """Close database connection after request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database and create users table."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
        ''')
        
        # Add test users if table is empty
        cursor.execute('SELECT COUNT(*) FROM users')
        if cursor.fetchone()[0] == 0:
            test_users = [
                ('Ivan Ivanov', 'ivan@example.com'),
                ('Petr Petrov', 'petr@example.com'),
                ('Anna Sidorova', 'anna@example.com'),
            ]
            cursor.executemany('INSERT INTO users (name, email) VALUES (?, ?)', test_users)
            db.commit()


@app.route('/users', methods=['GET'])
def get_users():
    """Returns list of all users."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, name, email FROM users')
    users = cursor.fetchall()
    
    result = []
    for user in users:
        result.append({
            'id': user['id'],
            'name': user['name'],
            'email': user['email']
        })
    
    return jsonify(result)


@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Returns user by id."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, name, email FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user['id'],
        'name': user['name'],
        'email': user['email']
    })


@app.route('/users', methods=['POST'])
def create_user():
    """Create a new user."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Нет данных'}), 400
    
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    
    if not name:
        return jsonify({'error': 'Имя обязательно'}), 400
    if not email:
        return jsonify({'error': 'Email обязателен'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('INSERT INTO users (name, email) VALUES (?, ?)', (name, email))
        db.commit()
        user_id = cursor.lastrowid
        return jsonify({
            'id': user_id,
            'name': name,
            'email': email
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Пользователь с таким email уже существует'}), 409


# @app.route('/')
# def index():
#     """Serve the main HTML page."""
#     return send_from_directory('.', 'index.html')


@app.errorhandler(404)
def not_found(error):
    """Handle 404 error."""
    return jsonify({'error': 'Resource not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server error."""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
