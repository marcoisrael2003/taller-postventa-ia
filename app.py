import streamlit as st


st.set_page_config(
    page_title="Taller Postventa IA",
    page_icon="🚗",
    layout="wide",
)

st.title("🚗 Taller Postventa IA")

st.subheader(
    "Asistente inteligente para la gestión del servicio postventa"
)

st.write(
    """
    Utiliza el menú lateral para navegar por los diferentes módulos
    del sistema.
    """
)

st.divider()

columna_1, columna_2, columna_3, columna_4 = st.columns(4)

with columna_1:
    st.metric("Órdenes abiertas", "15")

with columna_2:
    st.metric("Vehículos en taller", "12")

with columna_3:
    st.metric("Productividad", "91 %")

with columna_4:
    st.metric("Facturación del día", "$2.350")

st.info(
    "Selecciona la opción Clientes en el menú lateral para consultar "
    "los registros almacenados en Supabase."
)