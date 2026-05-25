import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '123'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'votaciones'
    MYSQL_PASSWORD = 'Lr3rBD4Ecmhkd8Pt'
    MYSQL_DB = 'votaciones'