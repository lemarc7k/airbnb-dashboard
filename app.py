import streamlit as st
from streamlit_extras.switch_page_button import switch_page

st.set_page_config(page_title="Dashboard KM Ventures", layout="wide")

st.title("Airbnb Property Management Dashboard")
st.write("Bienvenido al panel de control de propiedades Airbnb. Usa el menú para navegar por los módulos.")

# Ejemplo: Redirección si haces clic
if st.button("Ir a Real Estate"):
    switch_page("real_estate")


# Estilos CSS mejorados
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: 'Segoe UI', 'Inter', sans-serif;
            background-color: #0f1115;
            color: white;
        }
        .navbar {
            display: flex;
            justify-content: center;
            gap: 50px;
            padding: 20px 0;
            background-color: #1a1a1d;
            border-bottom: 1px solid #333;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 999;
        }
        .navbar-item {
            color: white;
            text-decoration: none;
            position: relative;
            padding: 8px 12px;
            cursor: pointer;
        }
        .navbar-item:hover {
            color: #00ffe1;
        }
        .submenu {
            display: none;
            position: absolute;
            background-color: #1f1f22;
            margin-top: 12px;
            border-radius: 8px;
            overflow: hidden;
            min-width: 200px;
            box-shadow: 0 4px 12px rgba(0, 255, 225, 0.2);
        }
        .submenu a {
            display: block;
            padding: 10px;
            color: white;
            text-decoration: none;
            font-weight: 400;
        }
        .submenu a:hover {
            background-color: #00ffe1;
            color: black;
        }
        .navbar-item:hover .submenu {
            display: block;
        }
        .header-title {
            font-size: 48px;
            font-weight: 800;
            text-align: center;
            margin-top: 50px;
            color: #00ffe1;
            text-shadow: 0 0 10px #00ffe1;
        }
        .subtitle {
            text-align: center;
            margin-top: 10px;
            font-size: 18px;
            color: #aaa;
            margin-bottom: 50px;
        }
        .business-container {
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 30px;
        }
        .business-card {
            background: linear-gradient(to bottom right, #1c1c20, #2a2a2f);
            padding: 30px;
            border-radius: 16px;
            width: 200px;
            text-align: center;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .business-card:hover {
            transform: scale(1.05);
            box-shadow: 0 0 15px #00ffe1;
        }
        .footer {
            text-align: center;
            margin-top: 60px;
            font-size: 12px;
            color: #666;
        }
        .laser-line {
            width: 100%;
            height: 5px;
            background: linear-gradient(to right, #00ffe1, transparent, #00ffe1);
            margin: 50px 0;
            border-radius: 10px;
            animation: pulse 2s infinite ease-in-out;
        }
        @keyframes pulse {
            0% {opacity: 0.4;}
            50% {opacity: 1;}
            100% {opacity: 0.4;}
        }
    </style>
""", unsafe_allow_html=True)

# Menú superior
st.markdown("""
    <div class="navbar">
        <div class="navbar-item">Inicio</div>
        <div class="navbar-item">Quiénes somos</div>
        <div class="navbar-item">
            Business Units
            <div class="submenu">
                <a href="#">Real Estate</a>
                <a href="#">Transport</a>
                <a href="#">Cleaning</a>
                <a href="#">IA Services</a>
                <a href="#">Removals</a>
            </div>
        </div>
        <div class="navbar-item">
            Servicios
            <div class="submenu">
                <a href="#">Consultoría</a>
                <a href="#">Expansión Internacional</a>
                <a href="#">Inversiones Estratégicas</a>
            </div>
        </div>
        <div class="navbar-item">Contacto</div>
    </div>
""", unsafe_allow_html=True)

# Contenido principal
st.markdown("<div class='header-title'>Construyendo el futuro, juntos.</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Innovación y excelencia en cada sector: Real Estate, Transporte, Limpieza, Inteligencia Artificial y más.</div>", unsafe_allow_html=True)

st.markdown("""
<div class="business-container">
    <div class="business-card">REAL ESTATE</div>
    <div class="business-card">TRANSPORT</div>
    <div class="business-card">CLEANING</div>
    <div class="business-card">IA SERVICES</div>
    <div class="business-card">REMOVALS</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='laser-line'></div>", unsafe_allow_html=True)

st.markdown("<div class='footer'>Nuestra misión es liderar con integridad y compromiso, aportando soluciones innovadoras que generan valor y crecimiento.<br>KM Ventures ©2025</div>", unsafe_allow_html=True)
