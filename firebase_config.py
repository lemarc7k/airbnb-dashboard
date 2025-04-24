import firebase_admin
from firebase_admin import credentials, firestore

# Ruta al archivo JSON de tu clave privada
cred = credentials.Certificate("firebase_key.json")

# Inicializa Firebase si aún no está inicializado
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# Referencia a Firestore
db = firestore.client()
