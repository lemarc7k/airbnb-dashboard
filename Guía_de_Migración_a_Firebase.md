# Guía de Migración Completa a Firebase

Este documento describe paso a paso cómo migramos la aplicación de gestión de reservas estilo Airbnb desde un sistema basado en archivos `.csv` hacia una arquitectura moderna 100% en Firebase (Firestore). Esta guía está pensada para que cualquier miembro del equipo pueda replicar el proceso en nuevos proyectos.

---

## 📁 Estructura Original del Proyecto

- Carpeta `data/` con archivos:
  - `bookings.csv`
  - `cleaning_schedule.csv`
  - `gastos.csv`
  - `incidents.csv`
  - `inventory.csv`
  - `reports.csv`
- Archivos `pages/*.py` que usaban `pd.read_csv()` para cargar datos.

---

## 🚀 Objetivo Final

- Eliminar dependencia de archivos `.csv` locales.
- Usar Firebase Firestore como base de datos principal.
- Permitir sincronización en tiempo real entre equipos.
- Asegurar persistencia y acceso en la nube.

---

## 📆 Paso a Paso de la Migración

### 1. ➕ Crear Firebase Project

- Ir a [https://console.firebase.google.com](https://console.firebase.google.com)
- Crear nuevo proyecto (ej: `airbnb-dashboard`)
- Activar Firestore Database (modo Production).

### 2. 🚚 Configurar Firebase en el proyecto

- Descargar archivo JSON de credenciales desde la sección **Project Settings > Service Accounts**.
- Guardar como: `firebase/credentials.json`

### 3. 🔍 Crear `firebase_config.py`

```python
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("firebase/credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
```

### 4. ♻️ Reemplazar `pd.read_csv` por `db.collection(...).stream()`

**Ejemplo** (para `bookings.csv`):

```python
# Antes:
df = pd.read_csv("data/bookings.csv")

# Después:
docs = db.collection("bookings").stream()
data = [doc.to_dict() for doc in docs]
df = pd.DataFrame(data)
```

### 5. 📝 Crear funciones de escritura y actualización

```python
def guardar_reserva(data):
    db.collection("bookings").add(data)

def actualizar_reserva(id, data):
    db.collection("bookings").document(id).update(data)

def eliminar_reserva(id):
    db.collection("bookings").document(id).delete()
```

### 6. 🔄 Ajustar formularios `st.form()` para usar Firebase

- En lugar de guardar en CSV, usar las funciones anteriores.

### 7. ✅ Confirmar estructura en Firestore

Cada colección debe tener estos nombres:

- `bookings`
- `cleaning`
- `inventory`
- `incidents`
- `gastos`
- `reports`

---

## 📥 Buenas prácticas finales

- 🔒 **Nunca subir `credentials.json` a GitHub.** Añade a `.gitignore`.
- 📊 Asegúrate de tener control de errores si `doc.to_dict()` da `None`.
- ✅ Usa `@st.cache_data` para acelerar la carga de datos.
- ✏️ Usa claves seguras y controladas en `secrets.toml` si publicas en Streamlit Cloud.

---

## 💡 Recomendaciones para nuevos proyectos

1. Clonar este repositorio como plantilla.
2. Crear nuevo proyecto Firebase por cada cliente o aplicación.
3. Seguir esta guía paso a paso.
4. Validar siempre desde el panel de Firestore si los datos se están guardando correctamente.
5. Considerar migrar también a Firebase Hosting o autenticar usuarios si el proyecto crece.

---

## 🚀 Estado actual

- [x] Migrado: Calendario
- [x] Migrado: Limpiezas
- [x] Migrado: Inventario
- [x] Migrado: Incidentes
- [x] Migrado: Reportes
- [x] Migrado: Dashboard KPIs
- [x] Migrado: Gestión de gastos

---

## 📅 Fecha de migración: Abril 2025

**Responsable:** Kevin Vera  
**Repositorio local:** `airbnb_dashboard/`
