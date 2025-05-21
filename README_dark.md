
# 📊 Real Estate Dashboard (Streamlit + Firebase)

Este proyecto es un dashboard de gestión de propiedades tipo Airbnb construido con **Streamlit** y sincronizado con **Firebase Firestore**. Ofrece visualización avanzada de ingresos, gastos, ocupación y análisis inteligente, todo en un solo archivo (`real_estate_optimizado_dark.py`).

---

## 🎨 MODO OSCURO FORZADO (ESTILO JARVIS)

La app utiliza un diseño profesional y futurista **forzado en modo oscuro** para asegurar:

- Máxima legibilidad.
- Impacto visual sofisticado.
- Coherencia con la estética tipo JARVIS / tech CEO.

> ⚠️ El modo claro está desactivado para evitar problemas de contraste o visibilidad.

---

## 📁 ESTRUCTURA GENERAL DEL ARCHIVO

El archivo está organizado por secciones principales, marcadas con encabezados visuales como:

```python
# ====================================================================================================
# === TAB INICIO =====================================================================================
# ====================================================================================================
```

Cada sección contiene subsecciones lógicas bien definidas.

---

## 🔧 FUNCIONES COMUNES

Ubicadas al inicio bajo:

```python
# === FUNCIONES COMUNES ===
```

Estas funciones centralizan la lógica de:

- `calcular_ingresos_diarios(df, inicio, fin)`
- `calcular_gastos_periodo(df_gastos, inicio, fin)`
- `calcular_ocupacion(df, inicio, fin)`

Así se evita la duplicación de código y se facilita el mantenimiento.

---

## 🧭 PESTAÑAS DISPONIBLES

| Pestaña   | Descripción |
|-----------|-------------|
| `INICIO`  | Panel visual con métricas semanales (ingresos, gastos, ocupación, beneficio) y JARVIS AI. |
| `GENERAL` | Análisis mensual de ingresos y ocupación con gráficos y tarjetas de resumen. |
| `RESERVAS`| Registro manual de bookings con autocalculo de limpieza y gasto variable + editor integrado. |
| `GASTOS`  | Visualización de gastos fijos y variables, comparativa contra ingresos por periodo. |
| `DETALLES`| Filtro por estado/mes para analizar reservas específicas y generar gráficos de ingresos. |

---

## 🧠 LÓGICAS FUNDAMENTALES

1. **Por estado de reserva ("pagado"/"pendiente")** → usada en `DETALLES` y otras pestañas para reflejar ingresos reales vs proyectados.
2. **Por periodo semanal automático** → usada en `INICIO` y `GASTOS` para análisis actualizado dinámico.

---

## 📂 Archivos importantes

- `real_estate_optimizado_dark.py` → código principal optimizado y con dark mode.
- `firebase_config.py` → inicializa la conexión a Firestore.
- `sync_firestore.py` → opcional para subir CSVs como colecciones iniciales.
- `requirements.txt` → librerías necesarias.

---

## ✨ Autor

Creado por **Kevin**, con visión de ser uno de los mayores expertos en tecnología, IA y gestión de propiedades con automatización.
