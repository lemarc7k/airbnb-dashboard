from firebase_config import db

# Leer documentos de la colección "bookings"
bookings = db.collection("bookings").stream()

print("📦 Reservas encontradas en Firestore:")
for doc in bookings:
    print(f"{doc.id} => {doc.to_dict()}")
