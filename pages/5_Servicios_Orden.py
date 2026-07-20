import pandas as pd
import streamlit as st

from services.supabase_service import (
    actualizar_servicio_orden,
    crear_servicio_orden,
    obtener_ordenes_trabajo,
    obtener_servicios_orden,
)


# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Servicios de la orden",
    page_icon="🔧",
    layout="wide",
)

st.title("🔧 Servicios de las órdenes de trabajo")

st.caption(
    "Registro y seguimiento de los trabajos realizados "
    "en cada orden de servicio."
)


ESTADOS_SERVICIO = [
    "Pendiente",
    "En proceso",
    "Finalizado",
    "Cancelado",
]


SERVICIOS_FRECUENTES = [
    "Cambio de aceite y filtro",
    "Mantenimiento preventivo",
    "Diagnóstico electrónico",
    "Revisión del sistema de frenos",
    "Cambio de pastillas de freno",
    "Revisión de suspensión",
    "Alineación y balanceo",
    "Cambio de batería",
    "Reparación del sistema eléctrico",
    "Revisión del sistema de refrigeración",
    "Cambio de correa de distribución",
    "Mantenimiento de aire acondicionado",
    "Reparación de motor",
    "Reparación de transmisión",
    "Otro servicio",
]


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def obtener_codigo_orden(orden_id) -> str:
    try:
        return f"OT-{int(orden_id):05d}"
    except (TypeError, ValueError):
        return "OT-SIN-CÓDIGO"


def obtener_datos_vehiculo(orden: dict) -> dict:
    return orden.get("vehiculos") or {}


def obtener_descripcion_orden(orden: dict) -> str:
    orden_id = orden.get("id")
    vehiculo = obtener_datos_vehiculo(orden)

    placa = vehiculo.get("placa") or "Sin placa"
    marca = vehiculo.get("marca") or ""
    modelo = vehiculo.get("modelo") or ""
    anio = vehiculo.get("anio") or ""

    descripcion_vehiculo = " ".join(
        f"{marca} {modelo} {anio}".split()
    )

    return (
        f"{obtener_codigo_orden(orden_id)} - "
        f"{placa} - {descripcion_vehiculo}"
    )


def obtener_cliente_desde_orden(orden: dict) -> str:
    vehiculo = orden.get("vehiculos") or {}
    cliente = vehiculo.get("clientes") or {}

    nombre = (
        f'{cliente.get("nombres", "")} '
        f'{cliente.get("apellidos", "")}'
    ).strip()

    return nombre or "Cliente no identificado"


def obtener_tecnico_desde_orden(orden: dict) -> str:
    tecnico = orden.get("tecnicos") or {}

    nombre = (
        f'{tecnico.get("nombres", "")} '
        f'{tecnico.get("apellidos", "")}'
    ).strip()

    return nombre or "Sin técnico asignado"


def obtener_descripcion_servicio(
    servicio: dict,
) -> str:
    servicio_id = servicio.get("id")
    descripcion = servicio.get("descripcion") or ""
    estado = servicio.get("estado") or ""

    return (
        f"Servicio #{servicio_id} - "
        f"{descripcion} - {estado}"
    )


# =========================================================
# MENSAJES
# =========================================================

if "mensaje_servicio" in st.session_state:
    st.success(
        st.session_state.pop("mensaje_servicio")
    )


# =========================================================
# CARGAR INFORMACIÓN
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
    servicios = obtener_servicios_orden()
except Exception as error:
    st.error(
        "No fue posible cargar los servicios. "
        f"Detalle: {error}"
    )
    servicios = []


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
        "Servicios registrados",
        "Nuevo servicio",
        "Editar servicio",
    ]
)


# =========================================================
# LISTADO DE SERVICIOS
# =========================================================

with tab_lista:
    st.subheader("Servicios registrados")

    if not servicios:
        st.info(
            "Todavía no existen servicios registrados."
        )

    else:
        filas = []

        for servicio in servicios:
            orden = (
                servicio.get("ordenes_trabajo")
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
                    "ID": servicio.get("id"),
                    "Orden": obtener_codigo_orden(
                        servicio.get("orden_id")
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
                    "Servicio": servicio.get(
                        "descripcion"
                    ),
                    "Cantidad": servicio.get("cantidad"),
                    "Precio unitario": servicio.get(
                        "precio_unitario"
                    ),
                    "Subtotal": servicio.get("subtotal"),
                    "Estado": servicio.get("estado"),
                    "Observaciones": servicio.get(
                        "observaciones"
                    ),
                    "Activo": servicio.get(
                        "activo",
                        True,
                    ),
                }
            )

        dataframe = pd.DataFrame(filas)

        filtro_1, filtro_2, filtro_3 = st.columns(3)

        with filtro_1:
            filtro_estado = st.selectbox(
                "Filtrar por estado",
                options=["Todos"] + ESTADOS_SERVICIO,
                key="filtro_estado_servicios",
            )

        with filtro_2:
            filtro_orden = st.selectbox(
                "Filtrar por orden",
                options=["Todas"]
                + sorted(
                    dataframe["Orden"]
                    .dropna()
                    .unique()
                    .tolist()
                ),
                key="filtro_orden_servicios",
            )

        with filtro_3:
            busqueda = st.text_input(
                "Buscar servicio, vehículo o cliente",
                key="busqueda_servicios",
            )

        dataframe_filtrado = dataframe.copy()

        if filtro_estado != "Todos":
            dataframe_filtrado = dataframe_filtrado[
                dataframe_filtrado["Estado"]
                == filtro_estado
            ]

        if filtro_orden != "Todas":
            dataframe_filtrado = dataframe_filtrado[
                dataframe_filtrado["Orden"]
                == filtro_orden
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

        total_servicios = len(dataframe)

        pendientes = int(
            (
                dataframe["Estado"]
                == "Pendiente"
            ).sum()
        )

        en_proceso = int(
            (
                dataframe["Estado"]
                == "En proceso"
            ).sum()
        )

        finalizados = int(
            (
                dataframe["Estado"]
                == "Finalizado"
            ).sum()
        )

        valor_total = pd.to_numeric(
            dataframe["Subtotal"],
            errors="coerce",
        ).fillna(0).sum()

        metrica_1, metrica_2, metrica_3, metrica_4, metrica_5 = (
            st.columns(5)
        )

        metrica_1.metric(
            "Total servicios",
            total_servicios,
        )

        metrica_2.metric(
            "Pendientes",
            pendientes,
        )

        metrica_3.metric(
            "En proceso",
            en_proceso,
        )

        metrica_4.metric(
            "Finalizados",
            finalizados,
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
            f"Servicios mostrados: "
            f"{len(dataframe_filtrado)} de "
            f"{len(dataframe)}"
        )


# =========================================================
# NUEVO SERVICIO
# =========================================================

with tab_nuevo:
    st.subheader(
        "Registrar servicio en una orden"
    )

    if not ordenes_por_id:
        st.warning(
            "Primero debes registrar al menos una orden "
            "de trabajo."
        )

    else:
        with st.form(
            "formulario_nuevo_servicio",
            clear_on_submit=True,
        ):
            orden_id = st.selectbox(
                "Orden de trabajo *",
                options=list(
                    ordenes_por_id.keys()
                ),
                format_func=lambda identificador: (
                    obtener_descripcion_orden(
                        ordenes_por_id[
                            identificador
                        ]
                    )
                ),
            )

            orden_seleccionada = (
                ordenes_por_id[orden_id]
            )

            columna_info_1, columna_info_2 = (
                st.columns(2)
            )

            with columna_info_1:
                st.info(
                    "Cliente: "
                    f"{obtener_cliente_desde_orden(
                        orden_seleccionada
                    )}"
                )

            with columna_info_2:
                st.info(
                    "Técnico: "
                    f"{obtener_tecnico_desde_orden(
                        orden_seleccionada
                    )}"
                )

            columna_1, columna_2 = st.columns(2)

            with columna_1:
                tipo_servicio = st.selectbox(
                    "Servicio frecuente",
                    options=SERVICIOS_FRECUENTES,
                )

                descripcion_personalizada = (
                    st.text_input(
                        "Descripción personalizada",
                        placeholder=(
                            "Escriba una descripción "
                            "cuando seleccione Otro servicio."
                        ),
                    )
                )

                cantidad = st.number_input(
                    "Cantidad *",
                    min_value=0.01,
                    value=1.00,
                    step=1.00,
                    format="%.2f",
                )

            with columna_2:
                precio_unitario = st.number_input(
                    "Precio unitario ($) *",
                    min_value=0.0,
                    value=0.0,
                    step=0.50,
                    format="%.2f",
                )

                estado = st.selectbox(
                    "Estado del servicio *",
                    options=ESTADOS_SERVICIO,
                )

                subtotal_estimado = (
                    float(cantidad)
                    * float(precio_unitario)
                )

                st.metric(
                    "Subtotal",
                    f"${subtotal_estimado:,.2f}",
                )

            observaciones = st.text_area(
                "Observaciones",
                height=100,
            )

            guardar = st.form_submit_button(
                "Guardar servicio",
                use_container_width=True,
            )

            if guardar:
                if tipo_servicio == "Otro servicio":
                    descripcion = (
                        descripcion_personalizada.strip()
                    )
                else:
                    descripcion = tipo_servicio

                if not descripcion:
                    st.error(
                        "Debes escribir la descripción "
                        "del servicio."
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
                        "descripcion": descripcion,
                        "cantidad": float(cantidad),
                        "precio_unitario": float(
                            precio_unitario
                        ),
                        "estado": estado,
                        "observaciones": (
                            observaciones.strip()
                            or None
                        ),
                        "activo": True,
                    }

                    try:
                        crear_servicio_orden(datos)

                        st.session_state[
                            "mensaje_servicio"
                        ] = (
                            "Servicio registrado "
                            "correctamente."
                        )

                        st.rerun()

                    except Exception as error:
                        st.error(
                            "No fue posible registrar "
                            "el servicio. "
                            f"Detalle: {error}"
                        )


# =========================================================
# EDITAR SERVICIO
# =========================================================

with tab_editar:
    st.subheader(
        "Editar servicio registrado"
    )

    if not servicios:
        st.warning(
            "No existen servicios disponibles "
            "para editar."
        )

    else:
        servicios_por_id = {
            servicio["id"]: servicio
            for servicio in servicios
            if servicio.get("id") is not None
        }

        servicio_id = st.selectbox(
            "Seleccione un servicio",
            options=list(
                servicios_por_id.keys()
            ),
            format_func=lambda identificador: (
                obtener_descripcion_servicio(
                    servicios_por_id[
                        identificador
                    ]
                )
            ),
        )

        servicio_seleccionado = (
            servicios_por_id[servicio_id]
        )

        orden_actual_id = (
            servicio_seleccionado.get("orden_id")
        )

        opciones_ordenes = list(
            ordenes_por_id.keys()
        )

        indice_orden = (
            opciones_ordenes.index(
                orden_actual_id
            )
            if orden_actual_id
            in opciones_ordenes
            else 0
        )

        estado_actual = (
            servicio_seleccionado.get("estado")
            or "Pendiente"
        )

        indice_estado = (
            ESTADOS_SERVICIO.index(
                estado_actual
            )
            if estado_actual
            in ESTADOS_SERVICIO
            else 0
        )

        with st.form(
            f"formulario_editar_servicio_"
            f"{servicio_id}"
        ):
            editar_orden_id = st.selectbox(
                "Orden de trabajo *",
                options=opciones_ordenes,
                index=indice_orden,
                format_func=lambda identificador: (
                    obtener_descripcion_orden(
                        ordenes_por_id[
                            identificador
                        ]
                    )
                ),
            )

            columna_1, columna_2 = st.columns(2)

            with columna_1:
                editar_descripcion = st.text_input(
                    "Descripción del servicio *",
                    value=(
                        servicio_seleccionado.get(
                            "descripcion"
                        )
                        or ""
                    ),
                )

                editar_cantidad = st.number_input(
                    "Cantidad *",
                    min_value=0.01,
                    value=float(
                        servicio_seleccionado.get(
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
                        servicio_seleccionado.get(
                            "precio_unitario"
                        )
                        or 0
                    ),
                    step=0.50,
                    format="%.2f",
                )

                editar_estado = st.selectbox(
                    "Estado del servicio *",
                    options=ESTADOS_SERVICIO,
                    index=indice_estado,
                )

                editar_subtotal = (
                    float(editar_cantidad)
                    * float(editar_precio)
                )

                st.metric(
                    "Subtotal actualizado",
                    f"${editar_subtotal:,.2f}",
                )

            editar_observaciones = st.text_area(
                "Observaciones",
                value=(
                    servicio_seleccionado.get(
                        "observaciones"
                    )
                    or ""
                ),
                height=100,
            )

            editar_activo = st.checkbox(
                "Servicio activo",
                value=(
                    servicio_seleccionado.get(
                        "activo",
                        True,
                    )
                ),
            )

            actualizar = st.form_submit_button(
                "Actualizar servicio",
                use_container_width=True,
            )

            if actualizar:
                descripcion_actualizada = (
                    editar_descripcion.strip()
                )

                if not descripcion_actualizada:
                    st.error(
                        "La descripción del servicio "
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
                        "descripcion": (
                            descripcion_actualizada
                        ),
                        "cantidad": float(
                            editar_cantidad
                        ),
                        "precio_unitario": float(
                            editar_precio
                        ),
                        "estado": editar_estado,
                        "observaciones": (
                            editar_observaciones.strip()
                            or None
                        ),
                        "activo": editar_activo,
                    }

                    try:
                        actualizar_servicio_orden(
                            servicio_id,
                            datos_actualizados,
                        )

                        st.session_state[
                            "mensaje_servicio"
                        ] = (
                            "Servicio actualizado "
                            "correctamente."
                        )

                        st.rerun()

                    except Exception as error:
                        st.error(
                            "No fue posible actualizar "
                            "el servicio. "
                            f"Detalle: {error}"
                        )