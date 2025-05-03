import streamlit as st
import json
import os

# ACTIVAR O DESACTIVAR LOGIN GLOBAL
USE_LOGIN = False  # ← Cambia esto a True para activar el login

USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def login():
    if not USE_LOGIN:
        return  # ← Si el login está desactivado, salta directamente

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""

    users = load_users()

    if not st.session_state.logged_in:
        st.title("🔒 Login - KM Airbnb Dashboard")
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrar Usuario (admin)"])

        # INICIAR SESIÓN
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("Entrar")

                if submit:
                    if username in users and users[username] == password:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success(f"Bienvenido, {username}")
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")

        # REGISTRAR NUEVO USUARIO
        with tab2:
            with st.form("register_form"):
                new_user = st.text_input("Nuevo usuario")
                new_pass = st.text_input("Contraseña nueva", type="password")
                confirm = st.text_input("Confirmar contraseña", type="password")
                registrar = st.form_submit_button("Registrar")

                if registrar:
                    if st.session_state.username != "kevin":
                        st.warning("Solo el administrador puede registrar nuevos usuarios.")
                    elif new_user in users:
                        st.warning("Ese usuario ya existe.")
                    elif new_pass != confirm:
                        st.warning("Las contraseñas no coinciden.")
                    else:
                        users[new_user] = new_pass
                        save_users(users)
                        st.success(f"Usuario '{new_user}' creado correctamente ✅")
        st.stop()

    else:
        st.sidebar.markdown(f"👤 Usuario: **{st.session_state.username}**")
        if st.sidebar.button("Cerrar sesión", key="logout_button"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
