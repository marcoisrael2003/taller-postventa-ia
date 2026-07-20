from datetime import date, datetime

import pandas as pd
import streamlit as st

from services.supabase_service import (
    actualizar_orden_trabajo,
    crear_orden_trabajo,
    obtener_ordenes_trabajo,
    obtener_tecnicos,
    obtener_vehiculos,
)


# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Órdenes de trabajo",
    page_icon="🧾",
    layout="wide",
)

st.title("🧾 Gestión de órdenes de trabajo")
st.caption(
    "Registro, consulta, asignación y actualización "
    "de órdenes de servicio."
)


ESTADOS_ORDEN = [
    "Pendiente",
    "Diagnóstico",
    "En proceso",
    "En espera de repuestos",
    "Finalizada",
    "Entregada",
    "Cancelada",
]


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def convertir_fecha(
    valor,
    fecha_predeterminada: date | None = None,
) -> date:
    """
    Convierte fechas procedentes de Supabase a objetos date.
    """
    if fecha_predeterminada is None:
        fecha_predeterminada = date.today()

    if not valor:
        return fecha_predeterminada

    try:
        return date.fromisoformat(str(valor)[:10])
    except (TypeError, ValueError):
        return fecha_predeterminada


def obtener_nombre_cliente(vehiculo: dict) -> str:
    cliente = vehiculo.get("clientes") or {}

    nombre = (
        f'{cliente.get("nombres", "")} '
        f'{cliente.get("apellidos", "")}'
    ).strip()

    return nombre or "Cliente no identificado"


def obtener_descripcion_vehiculo(vehiculo: dict) -> str:
    placa = vehiculo.get("placa") or "Sin placa"
    marca = vehiculo.get("marca") or ""
    modelo = vehiculo.get("modelo") or ""
    anio = vehiculo.get("anio") or ""

    descripcion = f"{placa} - {marca} {modelo} {anio}"

    return " ".join(descripcion.split())


def obtener_nombre_tecnico(tecnico: dict | None) -> str:
    if not tecnico:
        return "Sin asignar"

    nombre = (
        f'{tecnico.get("nombres", "")} '
        f'{tecnico.get("apellidos", "")}'
    ).strip()

    return nombre or "Sin asignar"


def obtener_codigo_orden(orden_id) -> str:
    try:
        return f"OT-{int(orden_id):05d}"
    except (TypeError, ValueError):
        return "OT-SIN-CÓDIGO"


# =========================================================
# MENSAJES DESPUÉS DE ACTUALIZAR
# =========================================================

if "mensaje_orden" in st.session_state:
    st.success(st.session_state.pop("mensaje_orden"))


# =========================================================
# CARGA GENERAL DE DATOS
# =========================================================

try:
    vehiculos = obtener_vehiculos()
except Exception as error:
    st.error(
        "No se pudieron cargar los vehículos. "
        f"Detalle: {error}"
    )
    vehiculos = []

try:
    tecnicos = obtener_tecnicos()
except Exception as error:
    st.error(
        "No se pudieron cargar los técnicos. "
        f"Detalle: {error}"
    )
    tecnicos = []

vehiculos_activos = [
    vehiculo
    for vehiculo in vehiculos
    if vehiculo.get("activo", True)
]

tecnicos_activos = [
    tecnico
    for tecnico in tecnicos
    if tecnico.get("activo", True)
]

vehiculos_por_id = {
    vehiculo["id"]: vehiculo
    for vehiculo in vehiculos_activos
    if vehiculo.get("id") is not None
}

tecnicos_activos_por_id = {
    tecnico["id"]: tecnico
    for tecnico in tecnicos_activos
    if tecnico.get("id") is not None
}


# =========================================================
# PESTAÑAS
# =========================================================

tab_lista, tab_nueva, tab_editar = st.tabs(
    [
        "Órdenes registradas",
        "Nueva orden",
        "Editar orden",
    ]
)


# =========================================================
# ÓRDENES REGISTRADAS
# =========================================================

with tab_lista:
    st.subheader("Órdenes registradas")

    try:
        ordenes = obtener_ordenes_trabajo()
    except Exception as error:
        st.error(
            "No fue posible consultar las órdenes de trabajo. "
            f"Detalle: {error}"
        )
        ordenes = []

    if not ordenes:
        st.info(
            "Todavía no existen órdenes de trabajo registradas."
        )

    else:
        filas = []

        for orden in ordenes:
            vehiculo = orden.get("vehiculos") or {}
            cliente = vehiculo.get("clientes") or {}
            tecnico = orden.get("tecnicos") or {}

            nombre_cliente = (
                f'{cliente.get("nombres", "")} '
                f'{cliente.get("apellidos", "")}'
            ).strip()

            nombre_tecnico = obtener_nombre_tecnico(tecnico)

            filas.append(
                {
                    "Código": obtener_codigo_orden(
                        orden.get("id")
                    ),
                    "Fecha de ingreso": orden.get(
                        "fecha_ingreso"
                    ),
                    "Placa": vehiculo.get("placa")
                    or "Sin placa",
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
                    "Técnico": nombre_tecnico,
                    "Motivo de ingreso": orden.get(
                        "motivo_ingreso"
                    ),
                    "Estado": orden.get("estado"),
                    "Fecha estimada": orden.get(
                        "fecha_estimada_entrega"
                    ),
                    "Fecha real": orden.get(
                        "fecha_entrega_real"
                    ),
                    "Kilometraje": orden.get(
                        "kilometraje_ingreso"
                    ),
                    "Costo estimado": orden.get(
                        "costo_estimado"
                    ),
                    "Costo final": orden.get("costo_final"),
                    "Activo": orden.get("activo", True),
                }
            )

        dataframe = pd.DataFrame(filas)

        columna_filtro_1, columna_filtro_2, columna_filtro_3 = (
            st.columns(3)
        )

        with columna_filtro_1:
            filtro_estado = st.selectbox(
                "Filtrar por estado",
                options=["Todos"] + ESTADOS_ORDEN,
                key="filtro_estado_ordenes",
            )

        with columna_filtro_2:
            filtro_tecnico = st.selectbox(
                "Filtrar por técnico",
                options=[
                    "Todos",
                    "Sin asignar",
                ]
                + sorted(
                    [
                        nombre
                        for nombre in dataframe[
                            "Técnico"
                        ].dropna().unique().tolist()
                        if nombre != "Sin asignar"
                    ]
                ),
                key="filtro_tecnico_ordenes",
            )

        with columna_filtro_3:
            busqueda = st.text_input(
                "Buscar orden, placa, cliente o vehículo",
                key="busqueda_ordenes",
            )

        dataframe_filtrado = dataframe.copy()

        if filtro_estado != "Todos":
            dataframe_filtrado = dataframe_filtrado[
                dataframe_filtrado["Estado"]
                == filtro_estado
            ]

        if filtro_tecnico != "Todos":
            dataframe_filtrado = dataframe_filtrado[
                dataframe_filtrado["Técnico"]
                == filtro_tecnico
            ]

        if busqueda.strip():
            texto_busqueda = busqueda.strip().lower()

            mascara = dataframe_filtrado.astype(str).apply(
                lambda fila: fila.str.lower()
                .str.contains(
                    texto_busqueda,
                    na=False,
                    regex=False,
                )
                .any(),
                axis=1,
            )

            dataframe_filtrado = dataframe_filtrado[
                mascara
            ]

        total_ordenes = len(dataframe)
        ordenes_pendientes = int(
            dataframe["Estado"]
            .isin(
                [
                    "Pendiente",
                    "Diagnóstico",
                    "En proceso",
                    "En espera de repuestos",
                ]
            )
            .sum()
        )
        ordenes_finalizadas = int(
            dataframe["Estado"]
            .isin(["Finalizada", "Entregada"])
            .sum()
        )
        ordenes_sin_tecnico = int(
            (dataframe["Técnico"] == "Sin asignar").sum()
        )

        metrica_1, metrica_2, metrica_3, metrica_4 = (
            st.columns(4)
        )

        metrica_1.metric(
            "Total de órdenes",
            total_ordenes,
        )
        metrica_2.metric(
            "En atención",
            ordenes_pendientes,
        )
        metrica_3.metric(
            "Finalizadas/entregadas",
            ordenes_finalizadas,
        )
        metrica_4.metric(
            "Sin técnico",
            ordenes_sin_tecnico,
        )

        st.dataframe(
            dataframe_filtrado,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Costo estimado": st.column_config.NumberColumn(
                    "Costo estimado",
                    format="$ %.2f",
                ),
                "Costo final": st.column_config.NumberColumn(
                    "Costo final",
                    format="$ %.2f",
                ),
                "Activo": st.column_config.CheckboxColumn(
                    "Activo"
                ),
            },
        )

        st.caption(
            f"Órdenes mostradas: "
            f"{len(dataframe_filtrado)} de "
            f"{len(dataframe)}"
        )


# =========================================================
# NUEVA ORDEN
# =========================================================

with tab_nueva:
    st.subheader("Registrar nueva orden de trabajo")

    if not vehiculos_activos:
        st.warning(
            "Primero debes registrar al menos un vehículo "
            "activo."
        )

    else:
        opciones_vehiculos = list(
            vehiculos_por_id.keys()
        )

        opciones_tecnicos = [None] + list(
            tecnicos_activos_por_id.keys()
        )

        with st.form(
            "formulario_nueva_orden",
            clear_on_submit=True,
        ):
            columna_1, columna_2 = st.columns(2)

            with columna_1:
                vehiculo_id = st.selectbox(
                    "Vehículo *",
                    options=opciones_vehiculos,
                    format_func=lambda identificador: (
                        f"{obtener_descripcion_vehiculo(
                            vehiculos_por_id[identificador]
                        )} | "
                        f"{obtener_nombre_cliente(
                            vehiculos_por_id[identificador]
                        )}"
                    ),
                )

                tecnico_id = st.selectbox(
                    "Técnico responsable",
                    options=opciones_tecnicos,
                    format_func=lambda identificador: (
                        "Sin técnico asignado"
                        if identificador is None
                        else (
                            f'{tecnicos_activos_por_id[
                                identificador
                            ].get("nombres", "")} '
                            f'{tecnicos_activos_por_id[
                                identificador
                            ].get("apellidos", "")} - '
                            f'{tecnicos_activos_por_id[
                                identificador
                            ].get("especialidad", "")}'
                        )
                    ),
                )

                fecha_ingreso = st.date_input(
                    "Fecha de ingreso *",
                    value=date.today(),
                )

                kilometraje_ingreso = st.number_input(
                    "Kilometraje de ingreso",
                    min_value=0,
                    value=0,
                    step=1,
                )

                estado = st.selectbox(
                    "Estado inicial *",
                    options=ESTADOS_ORDEN,
                    index=0,
                )

            with columna_2:
                fecha_estimada_entrega = st.date_input(
                    "Fecha estimada de entrega",
                    value=date.today(),
                )

                costo_estimado = st.number_input(
                    "Costo estimado ($)",
                    min_value=0.0,
                    value=0.0,
                    step=0.50,
                    format="%.2f",
                )

                motivo_ingreso = st.text_area(
                    "Motivo de ingreso *",
                    height=110,
                    placeholder=(
                        "Describa el motivo por el cual "
                        "ingresa el vehículo."
                    ),
                )

                diagnostico = st.text_area(
                    "Diagnóstico inicial",
                    height=110,
                    placeholder=(
                        "Registre el diagnóstico inicial "
                        "si está disponible."
                    ),
                )

            observaciones = st.text_area(
                "Observaciones",
                height=90,
            )

            guardar_orden = st.form_submit_button(
                "Guardar orden de trabajo",
                use_container_width=True,
            )

            if guardar_orden:
                motivo_limpio = motivo_ingreso.strip()
                diagnostico_limpio = diagnostico.strip()
                observaciones_limpias = (
                    observaciones.strip()
                )

                if not motivo_limpio:
                    st.error(
                        "El motivo de ingreso es obligatorio."
                    )

                elif (
                    fecha_estimada_entrega
                    < fecha_ingreso
                ):
                    st.error(
                        "La fecha estimada de entrega no "
                        "puede ser anterior a la fecha "
                        "de ingreso."
                    )

                else:
                    datos_nueva_orden = {
                        "vehiculo_id": vehiculo_id,
                        "tecnico_id": tecnico_id,
                        "fecha_ingreso": (
                            fecha_ingreso.isoformat()
                        ),
                        "motivo_ingreso": motivo_limpio,
                        "diagnostico": (
                            diagnostico_limpio or None
                        ),
                        "estado": estado,
                        "observaciones": (
                            observaciones_limpias or None
                        ),
                        "fecha_estimada_entrega": (
                            fecha_estimada_entrega.isoformat()
                        ),
                        "fecha_entrega_real": None,
                        "costo_estimado": float(
                            costo_estimado
                        ),
                        "costo_final": None,
                        "kilometraje_ingreso": int(
                            kilometraje_ingreso
                        ),
                        "activo": True,
                    }

                    try:
                        crear_orden_trabajo(
                            datos_nueva_orden
                        )

                        st.session_state[
                            "mensaje_orden"
                        ] = (
                            "Orden de trabajo registrada "
                            "correctamente."
                        )

                        st.rerun()

                    except Exception as error:
                        st.error(
                            "No fue posible registrar la "
                            "orden de trabajo. "
                            f"Detalle: {error}"
                        )


# =========================================================
# EDITAR ORDEN
# =========================================================

with tab_editar:
    st.subheader("Editar orden de trabajo")

    try:
        ordenes_edicion = obtener_ordenes_trabajo()
    except Exception as error:
        st.error(
            "No fue posible cargar las órdenes para editar. "
            f"Detalle: {error}"
        )
        ordenes_edicion = []

    if not ordenes_edicion:
        st.warning(
            "No existen órdenes de trabajo disponibles "
            "para editar."
        )

    else:
        ordenes_por_id = {
            orden["id"]: orden
            for orden in ordenes_edicion
            if orden.get("id") is not None
        }

        orden_id = st.selectbox(
            "Seleccione una orden",
            options=list(ordenes_por_id.keys()),
            format_func=lambda identificador: (
                f"{obtener_codigo_orden(identificador)} - "
                f'{(
                    ordenes_por_id[identificador]
                    .get("vehiculos") or {}
                ).get("placa", "Sin placa")} - '
                f'{ordenes_por_id[identificador].get(
                    "estado",
                    "Sin estado"
                )}'
            ),
        )

        orden_seleccionada = ordenes_por_id[
            orden_id
        ]

        todos_los_vehiculos_por_id = {
            vehiculo["id"]: vehiculo
            for vehiculo in vehiculos
            if vehiculo.get("id") is not None
        }

        todos_los_tecnicos_por_id = {
            tecnico["id"]: tecnico
            for tecnico in tecnicos
            if tecnico.get("id") is not None
        }

        vehiculo_actual_id = (
            orden_seleccionada.get("vehiculo_id")
        )
        tecnico_actual_id = (
            orden_seleccionada.get("tecnico_id")
        )

        opciones_vehiculos_edicion = list(
            todos_los_vehiculos_por_id.keys()
        )

        opciones_tecnicos_edicion = [None] + list(
            todos_los_tecnicos_por_id.keys()
        )

        indice_vehiculo = (
            opciones_vehiculos_edicion.index(
                vehiculo_actual_id
            )
            if vehiculo_actual_id
            in opciones_vehiculos_edicion
            else 0
        )

        indice_tecnico = (
            opciones_tecnicos_edicion.index(
                tecnico_actual_id
            )
            if tecnico_actual_id
            in opciones_tecnicos_edicion
            else 0
        )

        estado_actual = orden_seleccionada.get(
            "estado",
            "Pendiente",
        )

        indice_estado = (
            ESTADOS_ORDEN.index(estado_actual)
            if estado_actual in ESTADOS_ORDEN
            else 0
        )

        fecha_ingreso_actual = convertir_fecha(
            orden_seleccionada.get("fecha_ingreso")
        )

        fecha_estimada_actual = convertir_fecha(
            orden_seleccionada.get(
                "fecha_estimada_entrega"
            ),
            fecha_ingreso_actual,
        )

        fecha_real_guardada = (
            orden_seleccionada.get(
                "fecha_entrega_real"
            )
        )

        tiene_fecha_entrega = bool(
            fecha_real_guardada
        )

        fecha_real_actual = convertir_fecha(
            fecha_real_guardada
        )

        with st.form(
            f"formulario_editar_orden_{orden_id}"
        ):
            st.markdown(
                f"### {obtener_codigo_orden(orden_id)}"
            )

            columna_1, columna_2 = st.columns(2)

            with columna_1:
                editar_vehiculo_id = st.selectbox(
                    "Vehículo *",
                    options=opciones_vehiculos_edicion,
                    index=indice_vehiculo,
                    format_func=lambda identificador: (
                        f"{obtener_descripcion_vehiculo(
                            todos_los_vehiculos_por_id[
                                identificador
                            ]
                        )} | "
                        f"{obtener_nombre_cliente(
                            todos_los_vehiculos_por_id[
                                identificador
                            ]
                        )}"
                    ),
                )

                editar_tecnico_id = st.selectbox(
                    "Técnico responsable",
                    options=opciones_tecnicos_edicion,
                    index=indice_tecnico,
                    format_func=lambda identificador: (
                        "Sin técnico asignado"
                        if identificador is None
                        else (
                            f'{todos_los_tecnicos_por_id[
                                identificador
                            ].get("nombres", "")} '
                            f'{todos_los_tecnicos_por_id[
                                identificador
                            ].get("apellidos", "")} - '
                            f'{todos_los_tecnicos_por_id[
                                identificador
                            ].get("especialidad", "")}'
                            + (
                                ""
                                if todos_los_tecnicos_por_id[
                                    identificador
                                ].get("activo", True)
                                else " (Inactivo)"
                            )
                        )
                    ),
                )

                editar_fecha_ingreso = st.date_input(
                    "Fecha de ingreso *",
                    value=fecha_ingreso_actual,
                )

                editar_kilometraje = st.number_input(
                    "Kilometraje de ingreso",
                    min_value=0,
                    value=int(
                        orden_seleccionada.get(
                            "kilometraje_ingreso"
                        )
                        or 0
                    ),
                    step=1,
                )

                editar_estado = st.selectbox(
                    "Estado *",
                    options=ESTADOS_ORDEN,
                    index=indice_estado,
                )

                editar_activo = st.checkbox(
                    "Orden activa",
                    value=orden_seleccionada.get(
                        "activo",
                        True,
                    ),
                )

            with columna_2:
                editar_fecha_estimada = st.date_input(
                    "Fecha estimada de entrega",
                    value=fecha_estimada_actual,
                )

                editar_costo_estimado = (
                    st.number_input(
                        "Costo estimado ($)",
                        min_value=0.0,
                        value=float(
                            orden_seleccionada.get(
                                "costo_estimado"
                            )
                            or 0
                        ),
                        step=0.50,
                        format="%.2f",
                    )
                )

                registrar_fecha_real = st.checkbox(
                    "Registrar fecha real de entrega",
                    value=tiene_fecha_entrega,
                )

                editar_fecha_real = st.date_input(
                    "Fecha real de entrega",
                    value=fecha_real_actual,
                    disabled=not registrar_fecha_real,
                )

                registrar_costo_final = st.checkbox(
                    "Registrar costo final",
                    value=(
                        orden_seleccionada.get(
                            "costo_final"
                        )
                        is not None
                    ),
                )

                editar_costo_final = st.number_input(
                    "Costo final ($)",
                    min_value=0.0,
                    value=float(
                        orden_seleccionada.get(
                            "costo_final"
                        )
                        or 0
                    ),
                    step=0.50,
                    format="%.2f",
                    disabled=not registrar_costo_final,
                )

            editar_motivo = st.text_area(
                "Motivo de ingreso *",
                value=orden_seleccionada.get(
                    "motivo_ingreso"
                )
                or "",
                height=100,
            )

            editar_diagnostico = st.text_area(
                "Diagnóstico",
                value=orden_seleccionada.get(
                    "diagnostico"
                )
                or "",
                height=110,
            )

            editar_observaciones = st.text_area(
                "Observaciones",
                value=orden_seleccionada.get(
                    "observaciones"
                )
                or "",
                height=90,
            )

            actualizar_orden = st.form_submit_button(
                "Actualizar orden de trabajo",
                use_container_width=True,
            )

            if actualizar_orden:
                motivo_actualizado = (
                    editar_motivo.strip()
                )
                diagnostico_actualizado = (
                    editar_diagnostico.strip()
                )
                observaciones_actualizadas = (
                    editar_observaciones.strip()
                )

                if not motivo_actualizado:
                    st.error(
                        "El motivo de ingreso es obligatorio."
                    )

                elif (
                    editar_fecha_estimada
                    < editar_fecha_ingreso
                ):
                    st.error(
                        "La fecha estimada de entrega no "
                        "puede ser anterior a la fecha "
                        "de ingreso."
                    )

                elif (
                    registrar_fecha_real
                    and editar_fecha_real
                    < editar_fecha_ingreso
                ):
                    st.error(
                        "La fecha real de entrega no puede "
                        "ser anterior a la fecha de ingreso."
                    )

                else:
                    datos_actualizados = {
                        "vehiculo_id": (
                            editar_vehiculo_id
                        ),
                        "tecnico_id": (
                            editar_tecnico_id
                        ),
                        "fecha_ingreso": (
                            editar_fecha_ingreso.isoformat()
                        ),
                        "motivo_ingreso": (
                            motivo_actualizado
                        ),
                        "diagnostico": (
                            diagnostico_actualizado
                            or None
                        ),
                        "estado": editar_estado,
                        "observaciones": (
                            observaciones_actualizadas
                            or None
                        ),
                        "fecha_estimada_entrega": (
                            editar_fecha_estimada
                            .isoformat()
                        ),
                        "fecha_entrega_real": (
                            editar_fecha_real.isoformat()
                            if registrar_fecha_real
                            else None
                        ),
                        "costo_estimado": float(
                            editar_costo_estimado
                        ),
                        "costo_final": (
                            float(editar_costo_final)
                            if registrar_costo_final
                            else None
                        ),
                        "kilometraje_ingreso": int(
                            editar_kilometraje
                        ),
                        "activo": editar_activo,
                    }

                    try:
                        actualizar_orden_trabajo(
                            orden_id,
                            datos_actualizados,
                        )

                        st.session_state[
                            "mensaje_orden"
                        ] = (
                            "Orden de trabajo actualizada "
                            "correctamente."
                        )

                        st.rerun()

                    except Exception as error:
                        st.error(
                            "No fue posible actualizar la "
                            "orden de trabajo. "
                            f"Detalle: {error}"
                        )