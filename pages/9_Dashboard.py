import pandas as pd
import streamlit as st

from services.supabase_service import (
    obtener_clientes,
    obtener_ordenes_trabajo,
    obtener_resumen_costos_orden,
    obtener_tecnicos,
    obtener_vehiculos,
)


# =========================================================
# CONFIGURACIÓN DE LA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Dashboard del taller")

st.caption(
    "Resumen general de clientes, vehículos, técnicos, "
    "órdenes de trabajo y costos del servicio postventa."
)


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def convertir_numero(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def crear_codigo_orden(orden_id) -> str:
    try:
        return f"OT-{int(orden_id):05d}"
    except (TypeError, ValueError):
        return "OT-SIN-CÓDIGO"


def formar_nombre(nombres, apellidos, alternativo) -> str:
    nombre = f"{nombres or ''} {apellidos or ''}".strip()

    return nombre or alternativo


def normalizar_estado(valor) -> str:
    estado = str(valor or "").strip()

    return estado or "Sin estado"


def normalizar_fecha(valor):
    fecha = pd.to_datetime(
        valor,
        errors="coerce",
    )

    if pd.isna(fecha):
        return None

    return fecha


# =========================================================
# CARGAR DATOS
# =========================================================

errores = []

try:
    clientes = obtener_clientes()
except Exception as error:
    clientes = []
    errores.append(
        f"No fue posible cargar los clientes: {error}"
    )

try:
    vehiculos = obtener_vehiculos()
except Exception as error:
    vehiculos = []
    errores.append(
        f"No fue posible cargar los vehículos: {error}"
    )

try:
    tecnicos = obtener_tecnicos()
except Exception as error:
    tecnicos = []
    errores.append(
        f"No fue posible cargar los técnicos: {error}"
    )

try:
    ordenes = obtener_ordenes_trabajo()
except Exception as error:
    ordenes = []
    errores.append(
        f"No fue posible cargar las órdenes: {error}"
    )

try:
    resumen_costos = obtener_resumen_costos_orden()
except Exception as error:
    resumen_costos = []
    errores.append(
        f"No fue posible cargar los costos: {error}"
    )


if errores:
    with st.expander(
        "Advertencias durante la carga de información"
    ):
        for mensaje in errores:
            st.warning(mensaje)


# =========================================================
# CÁLCULOS GENERALES
# =========================================================

total_clientes = len(clientes)

total_vehiculos = len(vehiculos)

total_tecnicos = len(tecnicos)

tecnicos_activos = sum(
    1
    for tecnico in tecnicos
    if tecnico.get("activo", True)
)

total_ordenes = len(ordenes)

ordenes_activas = sum(
    1
    for orden in ordenes
    if orden.get("activo", True)
)

total_servicios = sum(
    convertir_numero(
        registro.get("total_servicios")
    )
    for registro in resumen_costos
)

total_repuestos = sum(
    convertir_numero(
        registro.get("total_repuestos")
    )
    for registro in resumen_costos
)

total_general = sum(
    convertir_numero(
        registro.get("total_general")
    )
    for registro in resumen_costos
)


# =========================================================
# MÉTRICAS PRINCIPALES
# =========================================================

st.subheader("Resumen general")

fila_1_columna_1, fila_1_columna_2, fila_1_columna_3, fila_1_columna_4 = (
    st.columns(4)
)

fila_1_columna_1.metric(
    "Clientes registrados",
    total_clientes,
)

fila_1_columna_2.metric(
    "Vehículos registrados",
    total_vehiculos,
)

fila_1_columna_3.metric(
    "Técnicos activos",
    tecnicos_activos,
    delta=(
        f"{total_tecnicos} registrados"
    ),
)

fila_1_columna_4.metric(
    "Órdenes registradas",
    total_ordenes,
    delta=(
        f"{ordenes_activas} activas"
    ),
)


fila_2_columna_1, fila_2_columna_2, fila_2_columna_3 = (
    st.columns(3)
)

fila_2_columna_1.metric(
    "Total en servicios",
    f"${total_servicios:,.2f}",
)

fila_2_columna_2.metric(
    "Total en repuestos",
    f"${total_repuestos:,.2f}",
)

fila_2_columna_3.metric(
    "Total general",
    f"${total_general:,.2f}",
)


st.divider()


# =========================================================
# PREPARAR ÓRDENES
# =========================================================

filas_ordenes = []

for orden in ordenes:
    vehiculo = orden.get("vehiculos") or {}
    cliente = vehiculo.get("clientes") or {}
    tecnico = orden.get("tecnicos") or {}

    nombre_cliente = formar_nombre(
        cliente.get("nombres"),
        cliente.get("apellidos"),
        "Cliente no identificado",
    )

    nombre_tecnico = formar_nombre(
        tecnico.get("nombres"),
        tecnico.get("apellidos"),
        "Sin técnico asignado",
    )

    descripcion_vehiculo = " ".join(
        (
            f'{vehiculo.get("marca") or ""} '
            f'{vehiculo.get("modelo") or ""} '
            f'{vehiculo.get("anio") or ""}'
        ).split()
    )

    filas_ordenes.append(
        {
            "Orden": crear_codigo_orden(
                orden.get("id")
            ),
            "Orden ID": orden.get("id"),
            "Fecha de ingreso": normalizar_fecha(
                orden.get("fecha_ingreso")
            ),
            "Estado": normalizar_estado(
                orden.get("estado")
            ),
            "Placa": (
                vehiculo.get("placa")
                or "Sin placa"
            ),
            "Vehículo": (
                descripcion_vehiculo
                or "Sin información"
            ),
            "Cliente": nombre_cliente,
            "Técnico": nombre_tecnico,
            "Motivo de ingreso": (
                orden.get("motivo_ingreso")
                or orden.get("descripcion_problema")
                or orden.get("observaciones")
                or "Sin información"
            ),
            "Costo estimado": convertir_numero(
                orden.get("costo_estimado")
            ),
            "Activo": orden.get("activo", True),
        }
    )


dataframe_ordenes = pd.DataFrame(filas_ordenes)


# =========================================================
# GRÁFICOS DE ÓRDENES
# =========================================================

st.subheader("Análisis de órdenes de trabajo")

columna_grafico_1, columna_grafico_2 = st.columns(2)


with columna_grafico_1:
    st.markdown("#### Órdenes por estado")

    if dataframe_ordenes.empty:
        st.info(
            "No existen órdenes para mostrar."
        )

    else:
        ordenes_por_estado = (
            dataframe_ordenes["Estado"]
            .value_counts()
            .rename_axis("Estado")
            .to_frame("Cantidad")
        )

        st.bar_chart(
            ordenes_por_estado,
            use_container_width=True,
        )


with columna_grafico_2:
    st.markdown("#### Órdenes por técnico")

    if dataframe_ordenes.empty:
        st.info(
            "No existen órdenes para mostrar."
        )

    else:
        ordenes_por_tecnico = (
            dataframe_ordenes["Técnico"]
            .value_counts()
            .rename_axis("Técnico")
            .to_frame("Cantidad")
        )

        st.bar_chart(
            ordenes_por_tecnico,
            use_container_width=True,
        )


# =========================================================
# ESTADOS DE LAS ÓRDENES
# =========================================================

if not dataframe_ordenes.empty:
    estados = (
        dataframe_ordenes["Estado"]
        .value_counts()
        .to_dict()
    )

    st.markdown("#### Distribución de estados")

    columnas_estados = st.columns(
        max(1, min(len(estados), 5))
    )

    for indice, (estado, cantidad) in enumerate(
        estados.items()
    ):
        columna = columnas_estados[
            indice % len(columnas_estados)
        ]

        columna.metric(
            estado,
            cantidad,
        )


st.divider()


# =========================================================
# PREPARAR COSTOS
# =========================================================

filas_costos = []

for registro in resumen_costos:
    tecnico = formar_nombre(
        registro.get("tecnico_nombres"),
        registro.get("tecnico_apellidos"),
        "Sin técnico asignado",
    )

    cliente = formar_nombre(
        registro.get("cliente_nombres"),
        registro.get("cliente_apellidos"),
        "Cliente no identificado",
    )

    filas_costos.append(
        {
            "Orden": crear_codigo_orden(
                registro.get("orden_id")
            ),
            "Fecha de ingreso": normalizar_fecha(
                registro.get("fecha_ingreso")
            ),
            "Estado": normalizar_estado(
                registro.get("estado_orden")
            ),
            "Placa": (
                registro.get("placa")
                or "Sin placa"
            ),
            "Cliente": cliente,
            "Técnico": tecnico,
            "Total servicios": convertir_numero(
                registro.get("total_servicios")
            ),
            "Total repuestos": convertir_numero(
                registro.get("total_repuestos")
            ),
            "Total general": convertir_numero(
                registro.get("total_general")
            ),
        }
    )


dataframe_costos = pd.DataFrame(filas_costos)


# =========================================================
# GRÁFICOS DE COSTOS
# =========================================================

st.subheader("Análisis económico")

columna_costos_1, columna_costos_2 = st.columns(2)


with columna_costos_1:
    st.markdown("#### Servicios y repuestos por orden")

    if dataframe_costos.empty:
        st.info(
            "No existen valores económicos para mostrar."
        )

    else:
        grafico_costos_orden = (
            dataframe_costos[
                [
                    "Orden",
                    "Total servicios",
                    "Total repuestos",
                ]
            ]
            .set_index("Orden")
        )

        st.bar_chart(
            grafico_costos_orden,
            use_container_width=True,
        )


with columna_costos_2:
    st.markdown("#### Total generado por técnico")

    if dataframe_costos.empty:
        st.info(
            "No existen valores económicos para mostrar."
        )

    else:
        costos_por_tecnico = (
            dataframe_costos.groupby(
                "Técnico",
                dropna=False,
            )["Total general"]
            .sum()
            .sort_values(
                ascending=False
            )
            .to_frame()
        )

        st.bar_chart(
            costos_por_tecnico,
            use_container_width=True,
        )


st.divider()


# =========================================================
# FILTROS
# =========================================================

st.subheader("Consulta rápida de órdenes")

if dataframe_ordenes.empty:
    st.info(
        "No existen órdenes registradas."
    )

else:
    filtro_1, filtro_2, filtro_3 = st.columns(3)

    with filtro_1:
        estados_disponibles = sorted(
            dataframe_ordenes["Estado"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        estado_seleccionado = st.selectbox(
            "Estado",
            options=[
                "Todos",
                *estados_disponibles,
            ],
        )

    with filtro_2:
        tecnicos_disponibles = sorted(
            dataframe_ordenes["Técnico"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        tecnico_seleccionado = st.selectbox(
            "Técnico",
            options=[
                "Todos",
                *tecnicos_disponibles,
            ],
        )

    with filtro_3:
        busqueda = st.text_input(
            "Buscar",
            placeholder=(
                "Orden, placa, cliente o vehículo"
            ),
        )


    dataframe_filtrado = dataframe_ordenes.copy()


    if estado_seleccionado != "Todos":
        dataframe_filtrado = dataframe_filtrado[
            dataframe_filtrado["Estado"]
            == estado_seleccionado
        ]


    if tecnico_seleccionado != "Todos":
        dataframe_filtrado = dataframe_filtrado[
            dataframe_filtrado["Técnico"]
            == tecnico_seleccionado
        ]


    if busqueda.strip():
        texto = busqueda.strip().lower()

        mascara = dataframe_filtrado.astype(
            str
        ).apply(
            lambda fila: fila.str.lower()
            .str.contains(
                texto,
                na=False,
                regex=False,
            )
            .any(),
            axis=1,
        )

        dataframe_filtrado = (
            dataframe_filtrado[mascara]
        )


    tabla_ordenes = dataframe_filtrado.copy()

    tabla_ordenes["Fecha de ingreso"] = (
        pd.to_datetime(
            tabla_ordenes["Fecha de ingreso"],
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
    )


    st.dataframe(
        tabla_ordenes[
            [
                "Orden",
                "Fecha de ingreso",
                "Estado",
                "Placa",
                "Vehículo",
                "Cliente",
                "Técnico",
                "Costo estimado",
                "Activo",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Costo estimado": (
                st.column_config.NumberColumn(
                    "Costo estimado",
                    format="$ %.2f",
                )
            ),
            "Activo": (
                st.column_config.CheckboxColumn(
                    "Activo"
                )
            ),
        },
    )

    st.caption(
        f"Órdenes mostradas: "
        f"{len(dataframe_filtrado)} de "
        f"{len(dataframe_ordenes)}"
    )


st.divider()


# =========================================================
# ÚLTIMAS ÓRDENES
# =========================================================

st.subheader("Últimas órdenes registradas")

if dataframe_ordenes.empty:
    st.info(
        "No existen órdenes registradas."
    )

else:
    ultimas_ordenes = (
        dataframe_ordenes
        .sort_values(
            by="Fecha de ingreso",
            ascending=False,
            na_position="last",
        )
        .head(5)
        .copy()
    )

    ultimas_ordenes["Fecha de ingreso"] = (
        pd.to_datetime(
            ultimas_ordenes["Fecha de ingreso"],
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
    )

    st.dataframe(
        ultimas_ordenes[
            [
                "Orden",
                "Fecha de ingreso",
                "Estado",
                "Placa",
                "Cliente",
                "Técnico",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )