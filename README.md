# 🏠 Airbnb Property Management Dashboard

Este proyecto es un panel de control creado con **Streamlit** para la gestión de apartamentos estilo Airbnb. Permite visualizar y gestionar reservas, limpiezas, inventario, incidencias y reportes, todo desde el navegador.

---

## 🚀 ¿Qué incluye?

- 📅 Calendario de bookings
- 🧹 Limpiezas programadas
- 📦 Inventario de productos
- ⚠️ Reporte de incidencias
- 📊 Reportes semanales

---

## 🛠️ Requisitos

- Python 3.8 o superior
- pip

---

## 📦 Instalación

1. Clona el repositorio o descomprime este archivo zip en tu ordenador:

```bash
git clone https://github.com/tu-usuario/airbnb_dashboard.git
cd airbnb_dashboard
```

2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

3. Ejecuta la aplicación:

```bash
streamlit run app.py
```

---

## 🌐 ¿Cómo publicarlo online?

Puedes publicar esta app de forma gratuita usando [Streamlit Cloud](https://streamlit.io/cloud):

1. Crea una cuenta en Streamlit Cloud.
2. Sube este proyecto a un repositorio en GitHub.
3. Desde Streamlit Cloud, selecciona "New app", conecta tu repo, elige `app.py` como archivo principal y listo.

---

## 📁 Estructura del proyecto

```
airbnb_dashboard/
├── app.py
├── pages/
│   ├── 1_Bookings.py
│   ├── 2_Cleaning.py
│   ├── 3_Inventory.py
│   ├── 4_Incidents.py
│   └── 5_Reports.py
├── data/
│   ├── bookings.csv
│   ├── cleaning_schedule.csv
│   ├── inventory.csv
│   ├── incidents.csv
│   └── reports.csv
├── requirements.txt
└── README.md
```

---

## ✨ Siguiente paso

- Añadir login para cleaners/socios
- Conectar Google Sheets o base de datos real
- Automatizar tareas (alertas, emails, resúmenes)

¡Empieza ahora y lleva tu gestión Airbnb al siguiente nivel!

## ✨ SCRIPTS

.\venv\Scripts\activate

streamlit run app.py

##

streamlit cache clear
streamlit run home.py

## ✨ INTERPRETE

Presiona Ctrl + Shift + P

Escribe: python: Select Interpreter

Ahora debería salir el menú. Dale clic.

Selecciona la opción que tenga la ruta: .\venv\Scripts\python.exe

## ✨ actualizar el repositorio
