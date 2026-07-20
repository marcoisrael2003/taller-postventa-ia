import pandas as pd
import streamlit as st

from services.supabase_service import (
    obtener_resumen_costos_orden,
)


# =========================================================
# CONFIGURACIÓN DE LA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Resumen de costos",
    page_icon="💰",
    layout="wide",
)

st.title("💰 Resumen de costos de las órdenes")

st.caption(
    "Consulta automática del valor de los servicios, "
    "repuestos y total general de cada orden de trabajo."
)


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def crear_codigo_orden(orden_id) -> str:
    try:
        return f"OT-{int(orden_id):05d}"
    except (TypeError, ValueError):
        return "OT-SIN-CÓDIGO"


def obtener_nombre_completo(
    nombres,
    apellidos,
    texto_alternativo: str,
) -> str:
    nombre = f"{nombres or ''} {apellidos or ''}".strip()

    return nombre or texto_alternativo


def convertir_numero(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


# =========================================================
# CARGAR INFORMACIÓN
# =========================================================

try:
    resumen_costos = obtener_resumen_costos_orden()

except Exception as error:
    st.error(
        "No fue posible cargar el resumen de costos. "
        f"Detalle: {error}"
    )

    resumen_costos = []


# =========================================================
# VALIDAR INFORMACIÓN
# =========================================================

if not resumen_costos:
    st.info(
        "No existen órdenes disponibles para mostrar."
    )

    st.stop()


# =========================================================
# PREPARAR DATAFRAME
# =========================================================

filas = []

for registro in resumen_costos:
    cliente = obtener_nombre_completo(
        registro.get("cliente_nombres"),
        registro.get("cliente_apellidos"),
        "Cliente no identificado",
    )

    tecnico = obtener_nombre_completo(
        registro.get("tecnico_nombres"),
        registro.get("tecnico_apellidos"),
        "Sin técnico asignado",
    )

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
            "Cliente": cliente,
            "Técnico": tecnico,
            "Costo estimado": convertir_numero(
                registro.get("costo_estimado")
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
            "Costo final registrado": convertir_numero(
                registro.get("costo_final")
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
# MÉTRICAS GENERALES
# =========================================================

total_ordenes = len(dataframe)

ordenes_activas = int(
    dataframe["Activo"].fillna(False).sum()
)

total_servicios = dataframe[
    "Total servicios"
].sum()

total_repuestos = dataframe[
    "Total repuestos"
].sum()

total_general = dataframe[
    "Total general"
].sum()


metrica_1, metrica_2, metrica_3, metrica_4, metrica_5 = (
    st.columns(5)
)

metrica_1.metric(
    "Órdenes",
    total_ordenes,
)

metrica_2.metric(
    "Órdenes activas",
    ordenes_activas,
)

metrica_3.metric(
    "Servicios",
    f"${total_servicios:,.2f}",
)

metrica_4.metric(
    "Repuestos",
    f"${total_repuestos:,.2f}",
)

metrica_5.metric(
    "Total general",
    f"${total_general:,.2f}",
)


st.divider()


# =========================================================
# FILTROS
# =========================================================

st.subheader("Consulta de órdenes")

filtro_1, filtro_2, filtro_3 = st.columns(3)

with filtro_1:
    estados_disponibles = sorted(
        dataframe["Estado"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    filtro_estado = st.selectbox(
        "Filtrar por estado",
        options=["Todos"] + estados_disponibles,
    )


with filtro_2:
    placas_disponibles = sorted(
        dataframe["Placa"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    filtro_placa = st.selectbox(
        "Filtrar por placa",
        options=["Todas"] + placas_disponibles,
    )


with filtro_3:
    busqueda = st.text_input(
        "Buscar orden, cliente, técnico o vehículo",
        placeholder="Escriba un texto para buscar",
    )


dataframe_filtrado = dataframe.copy()


if filtro_estado != "Todos":
    dataframe_filtrado = dataframe_filtrado[
        dataframe_filtrado["Estado"]
        == filtro_estado
    ]


if filtro_placa != "Todas":
    dataframe_filtrado = dataframe_filtrado[
        dataframe_filtrado["Placa"]
        == filtro_placa
    ]


if busqueda.strip():
    texto = busqueda.strip().lower()

    mascara = dataframe_filtrado.astype(str).apply(
        lambda fila: fila.str.lower()
        .str.contains(
            texto,
            regex=False,
            na=False,
        )
        .any(),
        axis=1,
    )

    dataframe_filtrado = dataframe_filtrado[mascara]


# =========================================================
# TABLA GENERAL
# =========================================================

st.dataframe(
    dataframe_filtrado[
        [
            "Orden",
            "Fecha de ingreso",
            "Estado",
            "Placa",
            "Vehículo",
            "Cliente",
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

st.caption(
    f"Órdenes mostradas: {len(dataframe_filtrado)} "
    f"de {len(dataframe)}"
)


# =========================================================
# DETALLE DE UNA ORDEN
# =========================================================

st.divider()

st.subheader("Detalle económico de una orden")

ordenes_por_codigo = {
    fila["Orden"]: fila
    for fila in filas
}

orden_seleccionada = st.selectbox(
    "Seleccione una orden",
    options=list(ordenes_por_codigo.keys()),
)

detalle = ordenes_por_codigo[
    orden_seleccionada
]


detalle_1, detalle_2, detalle_3 = st.columns(3)

with detalle_1:
    st.markdown("#### Información de la orden")

    st.write(
        f"**Orden:** {detalle['Orden']}"
    )

    st.write(
        f"**Estado:** {detalle['Estado'] or 'Sin estado'}"
    )

    st.write(
        f"**Fecha de ingreso:** "
        f"{detalle['Fecha de ingreso'] or 'Sin fecha'}"
    )


with detalle_2:
    st.markdown("#### Vehículo y cliente")

    st.write(
        f"**Placa:** {detalle['Placa'] or 'Sin placa'}"
    )

    st.write(
        f"**Vehículo:** {detalle['Vehículo']}"
    )

    st.write(
        f"**Cliente:** {detalle['Cliente']}"
    )


with detalle_3:
    st.markdown("#### Responsable")

    st.write(
        f"**Técnico:** {detalle['Técnico']}"
    )

    st.write(
        f"**Orden activa:** "
        f"{'Sí' if detalle['Activo'] else 'No'}"
    )


st.markdown("#### Resumen económico")

costo_1, costo_2, costo_3, costo_4 = st.columns(4)

costo_1.metric(
    "Costo estimado",
    f"${detalle['Costo estimado']:,.2f}",
)

costo_2.metric(
    "Total servicios",
    f"${detalle['Total servicios']:,.2f}",
)

costo_3.metric(
    "Total repuestos",
    f"${detalle['Total repuestos']:,.2f}",
)

costo_4.metric(
    "Total general",
    f"${detalle['Total general']:,.2f}",
)


diferencia = (
    detalle["Total general"]
    - detalle["Costo estimado"]
)

if diferencia > 0:
    st.warning(
        "El total general supera el costo estimado en "
        f"${diferencia:,.2f}."
    )

elif diferencia < 0:
    st.success(
        "El total general está por debajo del costo "
        f"estimado en ${abs(diferencia):,.2f}."
    )

else:
    st.info(
        "El total general es igual al costo estimado."
    )


# =========================================================
# GRÁFICO
# =========================================================

st.divider()

st.subheader("Distribución de costos por orden")

datos_grafico = dataframe_filtrado[
    [
        "Orden",
        "Total servicios",
        "Total repuestos",
    ]
].set_index("Orden")

if datos_grafico.empty:
    st.info(
        "No existen datos para mostrar en el gráfico."
    )

else:
    st.bar_chart(
        datos_grafico,
        use_container_width=True,
    )