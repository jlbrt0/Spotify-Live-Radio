from backend import DATABASE, TOKEN, connect_database
import os, ast
from dotenv import load_dotenv
import empyrebase

DATABASE = None
TOKEN = None

def initialize_database():
    global DATABASE, TOKEN
    load_dotenv()
    config = ast.literal_eval(os.getenv('CONFIG'))
    email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')
    firebase = empyrebase.initialize_app(config)
    auth = firebase.auth()
    user = auth.sign_in_with_email_and_password(email, password)
    DATABASE = firebase.database()
    TOKEN = user['idToken']
    print("initialisation de la base de donnée")

def connect_database():
    global DATABASE, TOKEN
    try:
        DATABASE.child("Users/").get(token=TOKEN)
    except Exception:
        initialize_database()

def create_profil(username, user_id, name):
    connect_database()
    data_users = {username : {'user_id': user_id, 'name': name, 'friends' : ''}}
    data_telegram = {user_id : {'username': username, 'friends': ''}}
    DATABASE.child("Telegram").update(token=TOKEN, data=data_telegram)
    DATABASE.child("Users").update(token=TOKEN, data=data_users)

def update_profil(old_username, username, user_id, name):
    connect_database()
    username_friends_list = get_username_friend_list(old_username)

    DATABASE.child(f"Users/{old_username}").remove(token=TOKEN)
    DATABASE.child(f"Telegram/{user_id}/username").remove(token=TOKEN)

    data_telegram = {'username': username}
    data_users = {username : {'user_id': user_id, 'name': name, 'friends': username_friends_list}}

    DATABASE.child(f"Telegram/{user_id}").update(token=TOKEN, data=data_telegram)
    DATABASE.child(f"Users/").update(token=TOKEN, data=data_users)

def username_check(username):
    connect_database()
    username_list = DATABASE.child("Users").get(token=TOKEN).val()
    return not (username in username_list)

def id_check(user_id):
    connect_database()
    id_list = DATABASE.child("Telegram").get(token=TOKEN).val()

    return not (str(user_id) in id_list)

def add_friend(username, user_id, friend_username, friend_user_id):
    connect_database()
    data_users = {friend_username : ''}
    data_telegram = {friend_user_id : ''}
    DATABASE.child(f"Users/{username}/friends").update(token=TOKEN, data=data_users)
    DATABASE.child(f"Telegram/{user_id}/friends").update(token=TOKEN, data=data_telegram)

def get_username(user_id):
    connect_database()
    data = DATABASE.child(f"Telegram/{user_id}/username").get(token=TOKEN)
    return data.val()

def get_name(username):
    connect_database()
    data = DATABASE.child(f"Users/{username}/name").get(token=TOKEN)
    return data.val()

def get_id_friends_list(user_id):
    connect_database()
    data = DATABASE.child(f"Telegram/{user_id}/friends").get(token=TOKEN)    
    return data.val()

def get_username_friend_list(username):
    connect_database()
    data = DATABASE.child(f"Users/{username}/friends").get(token=TOKEN)    
    return data.val()

def get_user_id(username):
    connect_database()
    data = DATABASE.child(f"Users/{username}/user_id").get(token=TOKEN)
    return data.val()

# print(get_username(5295319047))
