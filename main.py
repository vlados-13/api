from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
CORS(app, origins="*")

app.config['SECRET_KEY'] = 'secret_key'

def load_users():
    if os.path.exists('data/users.json'):
        with open('data/users.json', 'r', encoding='utf-8') as json_file:
            return json.load(json_file)
    return []

def save_users(users):
    os.makedirs('data', exist_ok=True)
    with open('data/users.json', 'w', encoding='utf-8') as json_file:
        json.dump(users, json_file, ensure_ascii=False, indent=4)

def load_albums():
    if os.path.exists('data/albums.json'):
        with open('data/albums.json', 'r', encoding='utf-8') as json_file:
            return json.load(json_file)
    return []

def save_albums(albums):
    os.makedirs('data', exist_ok=True)
    with open('data/albums.json', 'w', encoding='utf-8') as json_file:
        json.dump(albums, json_file, ensure_ascii=False, indent=4)

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'message': 'Токен відсутній!'}), 403

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user_id']
        except Exception as e:
            return jsonify({'message': 'Невірний токен!'}), 403

        return f(current_user, *args, **kwargs)

    return decorated_function

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email або пароль відсутні!'}), 400

    users = load_users()

    for user in users:
        if user['email'] == data['email']:
            return jsonify({'message': 'Користувач з таким email вже існує!'}), 400

    new_user = {
        'id': len(users) + 1,
        'email': data['email'],
        'password': data['password']
    }

    users.append(new_user)
    save_users(users)
    return jsonify({'message': 'Користувача успішно зареєстровано!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    auth = request.get_json()

    if not auth or not auth.get('email') or not auth.get('password'):
        return jsonify({'message': 'Email або пароль відсутні!'}), 400

    users = load_users()

    user = None
    for u in users:
        if u['email'] == auth['email'] and u['password'] == auth['password']:
            user = u
            break

    if user:
        token = jwt.encode({'user_id': user['id'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'token': token})

    return jsonify({'message': 'Невірні дані для входу!'}), 401

albums = load_albums()

@app.route('/api/albums', methods=['GET'])
def get_albums():
    return jsonify(albums)

@app.route('/api/albums/<int:album_id>', methods=['GET'])
def get_album(album_id):
    album = None
    for a in albums:
        if a["id"] == album_id:
            album = a
            break
    if album:
        return jsonify(album)
    return jsonify({"error": "Альбом не знайдений"}), 404

@app.route('/api/albums', methods=['POST'])
@token_required
def create_album(current_user):
    data = request.get_json()
    new_album = {
        "id": len(albums) + 1,
        "title": data.get('title'),
        "year": data.get('year'),
        "number_of_songs": data.get('number_of_songs'),
        "cover_image": data.get('cover_image'),
        "album_link": data.get('album_link')
    }
    albums.append(new_album)
    save_albums(albums)
    return jsonify(new_album), 201

@app.route('/api/albums/<int:album_id>', methods=['PUT'])
@token_required
def update_album(current_user, album_id):
    data = request.get_json()
    album = None
    for a in albums:
        if a["id"] == album_id:
            album = a
            break
    if album:
        album["title"] = data.get('title', album["title"])
        album["year"] = data.get('year', album["year"])
        album["number_of_songs"] = data.get('number_of_songs', album["number_of_songs"])
        album["cover_image"] = data.get('cover_image', album["cover_image"])
        album["album_link"] = data.get('album_link', album["album_link"])

        save_albums(albums)
        return jsonify(album), 200
    return jsonify({"error": "Альбом не знайдений"}), 404

@app.route('/api/albums/<int:album_id>', methods=['DELETE'])
@token_required
def delete_album(current_user, album_id):
    global albums
    album_to_delete = None
    for album in albums:
        if album["id"] == album_id:
            album_to_delete = album
            break

    if album_to_delete:
        albums.remove(album_to_delete)
        save_albums(albums)
        return jsonify({"message": "Альбом успішно видалено"}), 200

    return jsonify({"error": "Альбом не знайдений"}), 404

if __name__ == "__main__":
    app.run(debug=True)
