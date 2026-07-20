import streamlit as st

# -----------------------------
# Configuración de la página
# -----------------------------
st.set_page_config(
    page_title="Taller Postventa IA",
    page_icon="🚗",
    layout="wide"
)

# -----------------------------
# Encabezado
# -----------------------------
st.title("🚗 Asistente Inteligente para la Gestión del Servicio Postventa")
st.markdown("### Proyecto de Titulación")

st.write(
    """
    Bienvenido al sistema inteligente de gestión del servicio postventa
    para talleres automotrices.

    Esta plataforma permitirá administrar:

    - 📋 Órdenes de trabajo
    - 🚗 Vehículos
    - 👨‍🔧 Técnicos
    - 👥 Clientes
    - 📦 Inventario
    - 📊 KPIs
    - 🤖 Asistente de Inteligencia Artificial
    """
)

st.divider()

# -----------------------------
# Indicadores de ejemplo
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Órdenes abiertas", "15")

with col2:
    st.metric("Vehículos en taller", "12")

with col3:
    st.metric("Productividad", "91 %")

with col4:
    st.metric("Facturación del día", "$2.350")

st.divider()

st.success("✅ Primera versión del sistema funcionando correctamente.")