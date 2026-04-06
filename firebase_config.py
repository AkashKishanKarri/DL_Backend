import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS")

if firebase_creds_json:
    try:
        cred_dict = json.loads(firebase_creds_json)
        cred = credentials.Certificate(cred_dict)
    except json.JSONDecodeError:
        raise ValueError("FIREBASE_CREDENTIALS environment variable is not valid JSON")
else:
    if not os.path.exists("serviceAccountKey.json"):
        raise FileNotFoundError("Missing serviceAccountKey.json or FIREBASE_CREDENTIALS environment variable.")
    cred = credentials.Certificate("serviceAccountKey.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()