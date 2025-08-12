import empyrebase
from dotenv import load_dotenv
import os
import ast


def connect_to_database():
    load_dotenv()
    config = os.getenv('CONFIG')
    config = ast.literal_eval(config)
    email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')

    firebase = empyrebase.initialize_app(config)

    auth = firebase.auth()
    user = auth.sign_in_with_email_and_password(email, password)

    db = firebase.database()
    token = user['idToken']

    database_information = (db, token)

    return database_information

def create_profile(database_information, user_id, user_name):
    database, token = database_information

    data = {user_id : {'friends' : '', 'username': user_name}}
    try:
        database.child("Users").update(token=token, data=data)
    except Exception:
        database, token = connect_to_database()
        database.child("Users").update(token=token, data=data)



def add_friend(database_information, user_id, friend_id):
    database, token = database_information

    data = {friend_id : ''}
    database.child(f"Users/{user_id}/friends").update(token=token, data=data)

def get_username(database_information, user_id):
    database, token = database_information

    try:
        data = database.child(f"Users/{user_id}/username").get(token=token)
    except Exception:
        database, token = connect_to_database()
        data = database.child(f"Users/{user_id}/username").get(token=token)

    return data.val()

def get_friends(database_information, user_id):
    database, token = database_information

    try:
        data = database.child(f"Users/{user_id}/friends").get(token=token)
    except Exception:
        database, token = connect_to_database()
        data = database.child(f"Users/{user_id}/friends").get(token=token)
        
    friends_dict = data.val()
    
    return friends_dict