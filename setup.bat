@echo off
echo 🛠 Activando entorno virtual...
call .venv\Scripts\activate

echo 🧩 Instalando librerías necesarias...
pip install -r requirements.txt

echo 🚀 Lanzando la aplicación...
streamlit run app.py

pause
