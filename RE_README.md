# 🏡 Real Estate Portal | KM Ventures - Presentación para el Equipo

---

## 📅 Estructura del Proyecto

```plaintext
airbnb_dashboard/
├── app.py               # Portal general KM Ventures
├── firebase_config.py    # Conexión Firebase
├── requirements.txt      # Dependencias
│
├── pages/
│   ├── real_estate.py    # Portal de Real Estate
│   └── modules/
│       ├── Registrar_Reserva.py
│       ├── Calendar Redesign.py
│       ├── Inventory.py
│       ├── Add_Gastos_Firestore.py
│       ├── Incidents.py
│       └── Reports.py
```

---

## 🔍 Qué Hace Cada Parte del Código

| Parte                  | Funcionalidad                                                         |
| :--------------------- | :-------------------------------------------------------------------- |
| `st.set_page_config()` | Configura nombre, icono y diseño. Solo al inicio en `real_estate.py`. |
| `session_state`        | Guarda la página activa (home, calendario, etc.).                     |
| `go_to(page)`          | Cambia la página activa dentro de `session_state`.                    |
| Botones Home           | Navegan entre módulos, usando `go_to()` + `st.rerun()`.               |
| Botón "Volver"         | Regresa a la página principal Real Estate.                            |
| `exec(open(...))`      | Carga los archivos de funcionalidades como Reservas, Gastos, etc.     |

---

## 🚨 Puntos Críticos a Tener Cuidado

- **NO repetir `st.set_page_config()`** dentro de los módulos.
- **Usar `st.rerun()`** siempre tras cambiar de página.
- **No modificar directamente `session_state`** fuera de `go_to()`.
- **Mantener los módulos limpios**: sin configuraciones globales.

---

## 🌟 Buenas Prácticas

- Cada nueva funcionalidad va a `/pages/modules/`.
- Los botones siempre llaman `go_to("nombre")` + `st.rerun()`.
- Modularizar el código si crece mucho.
- Documentar cada nuevo módulo brevemente.

---

## 🚀 Ejemplo de Navegación Interna

```python
if st.button("📘 Registrar Reserva"):
    go_to("registrar")
    st.rerun()
```

Cargar el módulo:

```python
elif st.session_state.real_estate_page == "registrar":
    if st.button("⬅️ Volver a Real Estate Home"):
        go_to("home")
        st.rerun()
    exec(open("pages/modules/Registrar_Reserva.py", encoding="utf-8").read())
```

---

# 💡 Mensaje Final

> ✅ Sistema modular, limpio y escalable para gestionar Real Estate.
>
> 📊 Mejora la productividad y facilita nuevas expansiones futuras.

# ACTUALIZAR GITHUB

git add .
git commit -m "Ultimas actualizaciones"
git push origin main
