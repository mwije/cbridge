from flask import current_app, session
import jwt
import datetime

def generate_jwt(user, conference, expiry=datetime.timedelta(hours=1), role=None):
    app_id = current_app.config['APP_ID']
    secret = current_app.config['APP_SECRET']
    domain = current_app.config['VIDEO_HOST_DOMAIN']
    room_name = conference.url

    if role==None: role=session['current_role']
    payload = {
           'aud': app_id,
           'iss': app_id,
           'sub': domain,
           'room': room_name,
           'exp': datetime.datetime.utcnow() + expiry,
           'moderator': role == 'clinician',
           'context': {
               'user': {
                   'id': user.uid,
                   'name': session['current_role'] + ': ' +user.name,
                   'email': 'user@example.com'
               }
           }
       }
    print(payload)
    token = jwt.encode(payload, secret, algorithm='HS256')
    return token