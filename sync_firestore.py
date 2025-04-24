import pandas as pd
from firebase_config import db

# Función genérica para sincronizar cualquier CSV con una colección
def sync_csv_to_firestore(csv_path, collection_name):
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        db.collection(collection_name).add(row.to_dict())
        print(f"✅ Añadido a {collection_name}: {row.to_dict()}")

# Sincronizar todos los archivos
sync_csv_to_firestore("data/bookings.csv", "bookings")
sync_csv_to_firestore("data/cleaning_schedule.csv", "cleaning")
sync_csv_to_firestore("data/gastos.csv", "gastos")
sync_csv_to_firestore("data/incidents.csv", "incidents")
sync_csv_to_firestore("data/inventory.csv", "inventory")
sync_csv_to_firestore("data/reports.csv", "reports")
