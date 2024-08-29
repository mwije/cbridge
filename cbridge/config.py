import os
import logging

class Config:
    SECRET_KEY = 'M3dm4l1nD4'
    DATABASE_NAME = 'testdb.db'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///./' + DATABASE_NAME
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APP_NAME_SHORT = "cBridge"
    APP_NAME = "clinical Bridge"
    VIDEO_HOST_URL = os.environ['CBRIDGE_VIDEO_URL'].strip('/') + '/'
    VIDEO_HOST_DOMAIN = os.environ['CBRIDGE_VIDEO_DOMAIN']

