import pandas as pd
import streamlit as st

from services.supabase_service import (
    actualizar_repuesto_orden,
    crear_repuesto_orden,
    obtener_ordenes_trabajo,
    obtener_repuestos_orden,
)


# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Repuestos de la orden",
    page_icon="⚙️",
    layout="wide",
)

st.title("⚙️ Repuestos de las órdenes de trabajo")

st.caption(
    "Registro y control de piezas, materiales y repuestos "
    "utilizados en cada orden."
)


REPUESTOS_FRECUENTES = [
    "Aceite de motor",
    "Filtro de aceite",
    "Filtro de aire",
    "Filtro de combustible",
    "Filtro de cabina",
    "Pastillas de freno",
    "Discos de freno",
    "Bujías",
    "Batería",
    "Correa de distribución",
    "Correa de accesorios",
    "Refrigerante",
    "Líquido de frenos",
    "Amortiguador",
    "Sensor",
    "Bombillo",
    "Fusible",
    "Otro repuesto",
]


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def obtener_codigo_orden(orden_id) -> str:
    try:
        return f"OT-{int(orden_id):05d}"
    except (TypeError, ValueError):
        return "OT-SIN-CÓDIGO"


def obtener_descripcion_orden(orden: dict) -> str:
    vehiculo = orden.get("vehiculos") or {}

    placa = vehiculo.get("placa") or "Sin placa"
    marca = vehiculo.get("marca") or ""
    modelo = vehiculo.get("modelo") or ""
    anio = vehiculo.get("anio") or ""

    descripcion_vehiculo = " ".join(
        f"{marca} {modelo} {anio}".split()
    )

    return (
        f"{obtener_codigo_orden(orden.get('id'))} - "
        f"{placa} - {descripcion_vehiculo}"
    )


def obtener_nombre_cliente(orden: dict) -> str:
    vehiculo = orden.get("vehiculos") or {}
    cliente = vehiculo.get("clientes") or {}

    nombre = (
        f'{cliente.get("nombres", "")} '
        f'{cliente.get("apellidos", "")}'
    ).strip()

    return nombre or "Cliente no identificado"


def obtener_nombre_tecnico(orden: dict) -> str:
    tecnico = orden.get("tecnicos") or {}

    nombre = (
        f'{tecnico.get("nombres", "")} '
        f'{tecnico.get("apellidos", "")}'
    ).strip()

    return nombre or "Sin técnico asignado"


def obtener_descripcion_repuesto(
    repuesto: dict,
) -> str:
    repuesto_id = repuesto.get("id")
    codigo = repuesto.get("codigo") or "Sin código"
    descripcion = repuesto.get("descripcion") or ""

    return (
        f"Repuesto #{repuesto_id} - "
        f"{codigo} - {descripcion}"
    )


# =========================================================
# MENSAJES
# =========================================================

if "mensaje_repuesto" in st.session_state:
    st.success(
        st.session_state.pop("mensaje_repuesto")
    )


# =========================================================
# CARGAR DATOS
# =========================================================

try:
    ordenes = obtener_ordenes_trabajo()
except Exception as error:
    st.error(
        "No fue posible cargar las órdenes de trabajo. "
        f"Detalle: {error}"
    )
    ordenes = []

try:
    repuestos = obtener_repuestos_orden()
except Exception as error:
    st.error(
        "No fue posible cargar los repuestos. "
        f"Detalle: {error}"
    )
    repuestos = []


ordenes_por_id = {
    orden["id"]: orden
    for orden in ordenes
    if orden.get("id") is not None
}


# =========================================================
# PESTAÑAS
# =========================================================

tab_lista, tab_nuevo, tab_editar = st.tabs(
    [
        "Repuestos registrados",
        "Nuevo repuesto",
        "Editar repuesto",
    ]
)


# =========================================================
# LISTADO
# =========================================================

with tab_lista:
    st.subheader("Repuestos registrados")

    if not repuestos:
        st.info(
            "Todavía no existen repuestos registrados."
        )

    else:
        filas = []

        for repuesto in repuestos:
            orden = (
                repuesto.get("ordenes_trabajo")
                or {}
            )

            vehiculo = orden.get("vehiculos") or {}
            cliente = vehiculo.get("clientes") or {}
            tecnico = orden.get("tecnicos") or {}

            nombre_cliente = (
                f'{cliente.get("nombres", "")} '
                f'{cliente.get("apellidos", "")}'
            ).strip()

            nombre_tecnico = (
                f'{tecnico.get("nombres", "")} '
                f'{tecnico.get("apellidos", "")}'
            ).strip()

            filas.append(
                {
                    "ID": repuesto.get("id"),
                    "Orden": obtener_codigo_orden(
                        repuesto.get("orden_id")
                    ),
                    "Código": (
                        repuesto.get("codigo")
                        or "Sin código"
                    ),
                    "Descripción": repuesto.get(
                        "descripcion"
                    ),
                    "Placa": (
                        vehiculo.get("placa")
                        or "Sin placa"
                    ),
                    "Vehículo": " ".join(
                        (
                            f'{vehiculo.get("marca", "")} '
                            f'{vehiculo.get("modelo", "")} '
                            f'{vehiculo.get("anio", "")}'
                        ).split()
                    ),
                    "Cliente": (
                        nombre_cliente
                        or "Cliente no identificado"
                    ),
                    "Técnico": (
                        nombre_tecnico
                        or "Sin técnico asignado"
                    ),
                    "Cantidad": repuesto.get("cantidad"),
                    "Precio unitario": repuesto.get(
                        "precio_unitario"
                    ),
                    "Subtotal": repuesto.get("subtotal"),
                    "Observaciones": repuesto.get(
                        "observaciones"
                    ),
                    "Activo": repuesto.get(
                        "activo",
                        True,
                    ),
                }
            )

        dataframe = pd.DataFrame(filas)

        filtro_1, filtro_2, filtro_3 = st.columns(3)

        with filtro_1:
            filtro_orden = st.selectbox(
                "Filtrar por orden",
                options=["Todas"]
                + sorted(
                    dataframe["Orden"]
                    .dropna()
                    .unique()
                    .tolist()
                ),
                key="filtro_orden_repuestos",
            )

        with filtro_2:
            filtro_activo = st.selectbox(
                "Filtrar por estado",
                options=[
                    "Todos",
                    "Activos",
                    "Inactivos",
                ],
                key="filtro_activo_repuestos",
            )

        with filtro_3:
            busqueda = st.text_input(
                "Buscar código, repuesto, placa o cliente",
                key="busqueda_repuestos",
            )

        dataframe_filtrado = dataframe.copy()

        if filtro_orden != "Todas":
            dataframe_filtrado = dataframe_filtrado[
                dataframe_filtrado["Orden"]
                == filtro_orden
            ]

        if filtro_activo == "Activos":
            dataframe_filtrado = dataframe_filtrado[
                dataframe_filtrado["Activo"] == True
            ]

        elif filtro_activo == "Inactivos":
            dataframe_filtrado = dataframe_filtrado[
                dataframe_filtrado["Activo"] == False
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

        total_repuestos = len(dataframe)

        repuestos_activos = int(
            dataframe["Activo"].fillna(False).sum()
        )

        repuestos_inactivos = (
            total_repuestos - repuestos_activos
        )

        cantidad_total = pd.to_numeric(
            dataframe["Cantidad"],
            errors="coerce",
        ).fillna(0).sum()

        valor_total = pd.to_numeric(
            dataframe["Subtotal"],
            errors="coerce",
        ).fillna(0).sum()

        metrica_1, metrica_2, metrica_3, metrica_4, metrica_5 = (
            st.columns(5)
        )

        metrica_1.metric(
            "Repuestos registrados",
            total_repuestos,
        )

        metrica_2.metric(
            "Activos",
            repuestos_activos,
        )

        metrica_3.metric(
            "Inactivos",
            repuestos_inactivos,
        )

        metrica_4.metric(
            "Cantidad total",
            f"{cantidad_total:,.2f}",
        )

        metrica_5.metric(
            "Valor total",
            f"${valor_total:,.2f}",
        )

        st.dataframe(
            dataframe_filtrado,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Cantidad": (
                    st.column_config.NumberColumn(
                        "Cantidad",
                        format="%.2f",
                    )
                ),
                "Precio unitario": (
                    st.column_config.NumberColumn(
                        "Precio unitario",
                        format="$ %.2f",
                    )
                ),
                "Subtotal": (
                    st.column_config.NumberColumn(
                        "Subtotal",
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
            f"Repuestos mostrados: "
            f"{len(dataframe_filtrado)} de "
            f"{len(dataframe)}"
        )


# =========================================================
# NUEVO REPUESTO
# =========================================================

with tab_nuevo:
    st.subheader(
        "Registrar repuesto en una orden"
    )

    if not ordenes_por_id:
        st.warning(
            "Primero debes registrar al menos una orden "
            "de trabajo."
        )

    else:
        with st.form(
            "formulario_nuevo_repuesto",
            clear_on_submit=True,
        ):
            orden_id = st.selectbox(
                "Orden de trabajo *",
                options=list(ordenes_por_id.keys()),
                format_func=lambda identificador: (
                    obtener_descripcion_orden(
                        ordenes_por_id[identificador]
                    )
                ),
            )

            orden_seleccionada = (
                ordenes_por_id[orden_id]
            )

            info_1, info_2 = st.columns(2)

            with info_1:
                st.info(
                    "Cliente: "
                    f"{obtener_nombre_cliente(
                        orden_seleccionada
                    )}"
                )

            with info_2:
                st.info(
                    "Técnico: "
                    f"{obtener_nombre_tecnico(
                        orden_seleccionada
                    )}"
                )

            columna_1, columna_2 = st.columns(2)

            with columna_1:
                tipo_repuesto = st.selectbox(
                    "Repuesto frecuente",
                    options=REPUESTOS_FRECUENTES,
                )

                descripcion_personalizada = (
                    st.text_input(
                        "Descripción personalizada",
                        placeholder=(
                            "Escriba el nombre cuando "
                            "seleccione Otro repuesto."
                        ),
                    )
                )

                codigo = st.text_input(
                    "Código del repuesto",
                    max_chars=50,
                    placeholder="Ejemplo: FIL-ACE-001",
                )

            with columna_2:
                cantidad = st.number_input(
                    "Cantidad *",
                    min_value=0.01,
                    value=1.00,
                    step=1.00,
                    format="%.2f",
                )

                precio_unitario = st.number_input(
                    "Precio unitario ($) *",
                    min_value=0.0,
                    value=0.0,
                    step=0.50,
                    format="%.2f",
                )

                subtotal = (
                    float(cantidad)
                    * float(precio_unitario)
                )

                st.metric(
                    "Subtotal",
                    f"${subtotal:,.2f}",
                )

            observaciones = st.text_area(
                "Observaciones",
                height=100,
            )

            guardar = st.form_submit_button(
                "Guardar repuesto",
                use_container_width=True,
            )

            if guardar:
                if tipo_repuesto == "Otro repuesto":
                    descripcion = (
                        descripcion_personalizada.strip()
                    )
                else:
                    descripcion = tipo_repuesto

                if not descripcion:
                    st.error(
                        "Debes ingresar la descripción "
                        "del repuesto."
                    )

                elif cantidad <= 0:
                    st.error(
                        "La cantidad debe ser mayor que cero."
                    )

                elif precio_unitario < 0:
                    st.error(
                        "El precio unitario no puede ser "
                        "negativo."
                    )

                else:
                    datos = {
                        "orden_id": orden_id,
                        "codigo": (
                            codigo.strip().upper()
                            or None
                        ),
                        "descripcion": descripcion,
                        "cantidad": float(cantidad),
                        "precio_unitario": float(
                            precio_unitario
                        ),
                        "observaciones": (
                            observaciones.strip()
                            or None
                        ),
                        "activo": True,
                    }

                    try:
                        crear_repuesto_orden(datos)

                        st.session_state[
                            "mensaje_repuesto"
                        ] = (
                            "Repuesto registrado "
                            "correctamente."
                        )

                        st.rerun()

                    except Exception as error:
                        st.error(
                            "No fue posible registrar "
                            "el repuesto. "
                            f"Detalle: {error}"
                        )


# =========================================================
# EDITAR REPUESTO
# =========================================================

with tab_editar:
    st.subheader(
        "Editar repuesto registrado"
    )

    if not repuestos:
        st.warning(
            "No existen repuestos disponibles "
            "para editar."
        )

    elif not ordenes_por_id:
        st.warning(
            "No existen órdenes de trabajo disponibles."
        )

    else:
        repuestos_por_id = {
            repuesto["id"]: repuesto
            for repuesto in repuestos
            if repuesto.get("id") is not None
        }

        repuesto_id = st.selectbox(
            "Seleccione un repuesto",
            options=list(repuestos_por_id.keys()),
            format_func=lambda identificador: (
                obtener_descripcion_repuesto(
                    repuestos_por_id[identificador]
                )
            ),
        )

        repuesto_seleccionado = (
            repuestos_por_id[repuesto_id]
        )

        orden_actual_id = (
            repuesto_seleccionado.get("orden_id")
        )

        opciones_ordenes = list(
            ordenes_por_id.keys()
        )

        indice_orden = (
            opciones_ordenes.index(
                orden_actual_id
            )
            if orden_actual_id in opciones_ordenes
            else 0
        )

        with st.form(
            f"formulario_editar_repuesto_{repuesto_id}"
        ):
            editar_orden_id = st.selectbox(
                "Orden de trabajo *",
                options=opciones_ordenes,
                index=indice_orden,
                format_func=lambda identificador: (
                    obtener_descripcion_orden(
                        ordenes_por_id[identificador]
                    )
                ),
            )

            columna_1, columna_2 = st.columns(2)

            with columna_1:
                editar_codigo = st.text_input(
                    "Código del repuesto",
                    value=(
                        repuesto_seleccionado.get(
                            "codigo"
                        )
                        or ""
                    ),
                    max_chars=50,
                )

                editar_descripcion = st.text_input(
                    "Descripción del repuesto *",
                    value=(
                        repuesto_seleccionado.get(
                            "descripcion"
                        )
                        or ""
                    ),
                )

                editar_cantidad = st.number_input(
                    "Cantidad *",
                    min_value=0.01,
                    value=float(
                        repuesto_seleccionado.get(
                            "cantidad"
                        )
                        or 1
                    ),
                    step=1.00,
                    format="%.2f",
                )

            with columna_2:
                editar_precio = st.number_input(
                    "Precio unitario ($) *",
                    min_value=0.0,
                    value=float(
                        repuesto_seleccionado.get(
                            "precio_unitario"
                        )
                        or 0
                    ),
                    step=0.50,
                    format="%.2f",
                )

                editar_activo = st.checkbox(
                    "Repuesto activo",
                    value=(
                        repuesto_seleccionado.get(
                            "activo",
                            True,
                        )
                    ),
                )

                subtotal_actualizado = (
                    float(editar_cantidad)
                    * float(editar_precio)
                )

                st.metric(
                    "Subtotal actualizado",
                    f"${subtotal_actualizado:,.2f}",
                )

            editar_observaciones = st.text_area(
                "Observaciones",
                value=(
                    repuesto_seleccionado.get(
                        "observaciones"
                    )
                    or ""
                ),
                height=100,
            )

            actualizar = st.form_submit_button(
                "Actualizar repuesto",
                use_container_width=True,
            )

            if actualizar:
                descripcion_actualizada = (
                    editar_descripcion.strip()
                )

                if not descripcion_actualizada:
                    st.error(
                        "La descripción del repuesto "
                        "es obligatoria."
                    )

                elif editar_cantidad <= 0:
                    st.error(
                        "La cantidad debe ser mayor "
                        "que cero."
                    )

                elif editar_precio < 0:
                    st.error(
                        "El precio unitario no puede "
                        "ser negativo."
                    )

                else:
                    datos_actualizados = {
                        "orden_id": editar_orden_id,
                        "codigo": (
                            editar_codigo.strip().upper()
                            or None
                        ),
                        "descripcion": (
                            descripcion_actualizada
                        ),
                        "cantidad": float(
                            editar_cantidad
                        ),
                        "precio_unitario": float(
                            editar_precio
                        ),
                        "observaciones": (
                            editar_observaciones.strip()
                            or None
                        ),
                        "activo": editar_activo,
                    }

                    try:
                        actualizar_repuesto_orden(
                            repuesto_id,
                            datos_actualizados,
                        )

                        st.session_state[
                            "mensaje_repuesto"
                        ] = (
                            "Repuesto actualizado "
                            "correctamente."
                        )

                        st.rerun()

                    except Exception as error:
                        st.error(
                            "No fue posible actualizar "
                            "el repuesto. "
                            f"Detalle: {error}"
                        )