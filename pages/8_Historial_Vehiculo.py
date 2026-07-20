import pandas as pd
import streamlit as st

from services.supabase_service import (
    obtener_historial_vehiculos,
)


# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Historial del vehículo",
    page_icon="🚗",
    layout="wide",
)

st.title("🚗 Historial del vehículo")

st.caption(
    "Consulta de órdenes de trabajo, servicios, repuestos "
    "y costos asociados a cada vehículo."
)


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def crear_codigo_orden(orden_id) -> str:
    try:
        return f"OT-{int(orden_id):05d}"
    except (TypeError, ValueError):
        return "OT-SIN-CÓDIGO"


def convertir_numero(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def formar_nombre(nombres, apellidos, alternativo) -> str:
    nombre = f"{nombres or ''} {apellidos or ''}".strip()
    return nombre or alternativo


# =========================================================
# CARGAR DATOS
# =========================================================

try:
    historial = obtener_historial_vehiculos()

except Exception as error:
    st.error(
        "No fue posible cargar el historial de vehículos. "
        f"Detalle: {error}"
    )
    historial = []


if not historial:
    st.info(
        "No existen órdenes registradas para mostrar."
    )
    st.stop()


# =========================================================
# PREPARAR DATOS
# =========================================================

filas = []

for registro in historial:
    vehiculo = " ".join(
        (
            f'{registro.get("marca") or ""} '
            f'{registro.get("modelo") or ""} '
            f'{registro.get("anio") or ""}'
        ).split()
    )

    filas.append(
        {
            "Orden": crear_codigo_orden(
                registro.get("orden_id")
            ),
            "Orden ID": registro.get("orden_id"),
            "Fecha de ingreso": registro.get(
                "fecha_ingreso"
            ),
            "Estado": registro.get("estado_orden"),
            "Placa": registro.get("placa"),
            "Vehículo": vehiculo or "Sin información",
            "Cliente": formar_nombre(
                registro.get("cliente_nombres"),
                registro.get("cliente_apellidos"),
                "Cliente no identificado",
            ),
            "Técnico": formar_nombre(
                registro.get("tecnico_nombres"),
                registro.get("tecnico_apellidos"),
                "Sin técnico asignado",
            ),
            "Total servicios": convertir_numero(
                registro.get("total_servicios")
            ),
            "Total repuestos": convertir_numero(
                registro.get("total_repuestos")
            ),
            "Total general": convertir_numero(
                registro.get("total_general")
            ),
            "Activo": registro.get("activo", True),
        }
    )


dataframe = pd.DataFrame(filas)

dataframe["Fecha de ingreso"] = pd.to_datetime(
    dataframe["Fecha de ingreso"],
    errors="coerce",
).dt.strftime("%Y-%m-%d")


# =========================================================
# SELECCIÓN DEL VEHÍCULO
# =========================================================

placas = sorted(
    dataframe["Placa"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

placa_seleccionada = st.selectbox(
    "Seleccione una placa",
    options=placas,
)

historial_vehiculo = dataframe[
    dataframe["Placa"] == placa_seleccionada
].copy()


if historial_vehiculo.empty:
    st.info(
        "No existen registros para la placa seleccionada."
    )
    st.stop()


# =========================================================
# INFORMACIÓN DEL VEHÍCULO
# =========================================================

ultimo_registro = historial_vehiculo.iloc[0]

info_1, info_2, info_3, info_4 = st.columns(4)

info_1.metric(
    "Placa",
    placa_seleccionada,
)

info_2.metric(
    "Vehículo",
    ultimo_registro["Vehículo"],
)

info_3.metric(
    "Cliente",
    ultimo_registro["Cliente"],
)

info_4.metric(
    "Visitas al taller",
    len(historial_vehiculo),
)


# =========================================================
# MÉTRICAS DEL HISTORIAL
# =========================================================

total_servicios = historial_vehiculo[
    "Total servicios"
].sum()

total_repuestos = historial_vehiculo[
    "Total repuestos"
].sum()

total_invertido = historial_vehiculo[
    "Total general"
].sum()


st.divider()

metrica_1, metrica_2, metrica_3 = st.columns(3)

metrica_1.metric(
    "Total en servicios",
    f"${total_servicios:,.2f}",
)

metrica_2.metric(
    "Total en repuestos",
    f"${total_repuestos:,.2f}",
)

metrica_3.metric(
    "Total acumulado",
    f"${total_invertido:,.2f}",
)


# =========================================================
# TABLA DEL HISTORIAL
# =========================================================

st.divider()

st.subheader(
    f"Historial de órdenes de {placa_seleccionada}"
)

st.dataframe(
    historial_vehiculo[
        [
            "Orden",
            "Fecha de ingreso",
            "Estado",
            "Técnico",
            "Total servicios",
            "Total repuestos",
            "Total general",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Total servicios": st.column_config.NumberColumn(
            "Total servicios",
            format="$ %.2f",
        ),
        "Total repuestos": st.column_config.NumberColumn(
            "Total repuestos",
            format="$ %.2f",
        ),
        "Total general": st.column_config.NumberColumn(
            "Total general",
            format="$ %.2f",
        ),
    },
)


# =========================================================
# DETALLE DE UNA VISITA
# =========================================================

st.divider()

st.subheader("Detalle de una visita")

ordenes_disponibles = (
    historial_vehiculo["Orden"]
    .dropna()
    .tolist()
)

orden_seleccionada = st.selectbox(
    "Seleccione una orden",
    options=ordenes_disponibles,
)

detalle = historial_vehiculo[
    historial_vehiculo["Orden"] == orden_seleccionada
].iloc[0]


detalle_1, detalle_2, detalle_3 = st.columns(3)

with detalle_1:
    st.markdown("#### Orden")

    st.write(
        f"**Código:** {detalle['Orden']}"
    )

    st.write(
        f"**Fecha:** {detalle['Fecha de ingreso']}"
    )

    st.write(
        f"**Estado:** {detalle['Estado'] or 'Sin estado'}"
    )


with detalle_2:
    st.markdown("#### Responsable")

    st.write(
        f"**Técnico:** {detalle['Técnico']}"
    )

    st.write(
        f"**Activo:** {'Sí' if detalle['Activo'] else 'No'}"
    )


with detalle_3:
    st.markdown("#### Costos")

    st.write(
        f"**Servicios:** "
        f"${detalle['Total servicios']:,.2f}"
    )

    st.write(
        f"**Repuestos:** "
        f"${detalle['Total repuestos']:,.2f}"
    )

    st.write(
        f"**Total:** "
        f"${detalle['Total general']:,.2f}"
    )


# =========================================================
# GRÁFICO
# =========================================================

st.divider()

st.subheader("Evolución de costos por visita")

datos_grafico = historial_vehiculo[
    [
        "Orden",
        "Total servicios",
        "Total repuestos",
    ]
].set_index("Orden")

st.bar_chart(
    datos_grafico,
    use_container_width=True,
)