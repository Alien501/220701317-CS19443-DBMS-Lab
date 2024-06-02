import pyrebase, os
from dotenv import load_dotenv

load_dotenv()

firebaseConfig = {
  'apiKey': os.getenv('apiKey'),
  'authDomain': os.getenv('authDomain'),
  'projectId': os.getenv('projectId'),
  'databaseURL': os.getenv('databaseURL'),
  'storageBucket': os.getenv('storageBucket'),
  'messagingSenderId': os.getenv('messagingSenderId'),
  'appId': os.getenv('appId')
}


firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()
auth = firebase.auth()