from datetime import date

import pandas as pd
import streamlit as st

from services.supabase_service import (
    actualizar_orden_trabajo,
    crear_orden_trabajo,
    obtener_ordenes_trabajo,
    obtener_vehiculos,
)


st.set_page_config(
    page_title="Órdenes de Trabajo",
    page_icon="📋",
    layout="wide",
)

st.title("📋 Órdenes de Trabajo")

ESTADOS_ORDEN = [
    "Abierta",
    "En diagnóstico",
    "En proceso",
    "Esperando repuestos",
    "Finalizada",
    "Entregada",
    "Cancelada",
]

if "mensaje_orden" in st.session_state:
    st.success(st.session_state.pop("mensaje_orden"))

tab_lista, tab_nueva, tab_editar = st.tabs(
    [
        "Órdenes registradas",
        "Nueva orden",
        "Editar orden",
    ]
)


# =========================================================
# LISTAR ÓRDENES
# =========================================================

with tab_lista:
    ordenes = obtener_ordenes_trabajo()

    if ordenes:
        filas = []

        for orden in ordenes:
            vehiculo = orden.get("vehiculos") or {}
            cliente = vehiculo.get("clientes") or {}

            propietario = (
                f'{cliente.get("nombres", "")} '
                f'{cliente.get("apellidos", "")}'
            ).strip()

            filas.append(
                {
                    "OT": orden.get("id"),
                    "Estado": orden.get("estado"),
                    "Placa": vehiculo.get("placa"),
                    "Vehículo": (
                        f'{vehiculo.get("marca", "")} '
                        f'{vehiculo.get("modelo", "")}'
                    ).strip(),
                    "Propietario": propietario,
                    "Cédula": cliente.get("cedula"),
                    "Fecha de ingreso": orden.get("fecha_ingreso"),
                    "Motivo": orden.get("motivo_ingreso"),
                    "Diagnóstico": orden.get("diagnostico"),
                    "Kilometraje": orden.get("kilometraje_ingreso"),
                    "Entrega estimada": (
                        orden.get("fecha_estimada_entrega")
                    ),
                    "Costo estimado": orden.get("costo_estimado"),
                    "Costo final": orden.get("costo_final"),
                    "Activo": orden.get("activo"),
                }
            )

        dataframe = pd.DataFrame(filas)

        columna_filtro_1, columna_filtro_2 = st.columns(2)

        with columna_filtro_1:
            estado_filtro = st.selectbox(
                "Filtrar por estado",
                options=["Todos"] + ESTADOS_ORDEN,
            )

        with columna_filtro_2:
            texto_busqueda = st.text_input(
                "Buscar por placa, propietario o motivo"
            )

        dataframe_filtrado = dataframe.copy()

        if estado_filtro != "Todos":
            dataframe_filtrado = dataframe_filtrado[
                dataframe_filtrado["Estado"] == estado_filtro
            ]

        if texto_busqueda.strip():
            busqueda = texto_busqueda.strip().lower()

            mascara = dataframe_filtrado.astype(str).apply(
                lambda fila: fila.str.lower().str.contains(
                    busqueda,
                    na=False,
                ).any(),
                axis=1,
            )

            dataframe_filtrado = dataframe_filtrado[mascara]

        st.dataframe(
            dataframe_filtrado,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            f"Total de órdenes mostradas: "
            f"{len(dataframe_filtrado)}"
        )

    else:
        st.warning(
            "No existen órdenes de trabajo registradas."
        )


# =========================================================
# CREAR ORDEN
# =========================================================

with tab_nueva:
    st.subheader("Registrar nueva orden de trabajo")

    vehiculos = obtener_vehiculos()

    vehiculos_activos = [
        vehiculo
        for vehiculo in vehiculos
        if vehiculo.get("activo", True)
    ]

    if not vehiculos_activos:
        st.warning(
            "Primero debes registrar al menos un vehículo activo."
        )

    else:
        vehiculos_por_id = {
            vehiculo["id"]: vehiculo
            for vehiculo in vehiculos_activos
        }

        with st.form(
            "formulario_nueva_orden",
            clear_on_submit=True,
        ):
            vehiculo_id = st.selectbox(
                "Vehículo *",
                options=list(vehiculos_por_id.keys()),
                format_func=lambda identificador: (
                    f'{vehiculos_por_id[identificador].get("placa", "")} - '
                    f'{vehiculos_por_id[identificador].get("marca", "")} '
                    f'{vehiculos_por_id[identificador].get("modelo", "")}'
                ),
            )

            columna_1, columna_2 = st.columns(2)

            with columna_1:
                motivo_ingreso = st.text_area(
                    "Motivo de ingreso *",
                    height=120,
                    placeholder=(
                        "Ejemplo: ruido en el motor, mantenimiento "
                        "preventivo, falla de frenos..."
                    ),
                )

                kilometraje_ingreso = st.number_input(
                    "Kilometraje de ingreso",
                    min_value=0,
                    value=0,
                    step=1,
                )

                costo_estimado = st.number_input(
                    "Costo estimado ($)",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    format="%.2f",
                )

            with columna_2:
                diagnostico = st.text_area(
                    "Diagnóstico inicial",
                    height=120,
                )

                fecha_estimada_entrega = st.date_input(
                    "Fecha estimada de entrega",
                    value=date.today(),
                )

                estado = st.selectbox(
                    "Estado inicial",
                    options=ESTADOS_ORDEN,
                    index=0,
                )

            observaciones = st.text_area(
                "Observaciones",
                placeholder=(
                    "Accesorios entregados, estado visual del vehículo, "
                    "nivel de combustible u otras novedades."
                ),
            )

            guardar = st.form_submit_button(
                "Guardar orden de trabajo",
                use_container_width=True,
            )

            if guardar:
                motivo_ingreso = motivo_ingreso.strip()
                diagnostico = diagnostico.strip()
                observaciones = observaciones.strip()

                if not motivo_ingreso:
                    st.error(
                        "El motivo de ingreso es obligatorio."
                    )

                else:
                    datos = {
                        "vehiculo_id": vehiculo_id,
                        "motivo_ingreso": motivo_ingreso,
                        "diagnostico": diagnostico or None,
                        "estado": estado,
                        "observaciones": observaciones or None,
                        "fecha_estimada_entrega": (
                            fecha_estimada_entrega.isoformat()
                        ),
                        "costo_estimado": float(costo_estimado),
                        "kilometraje_ingreso": int(
                            kilometraje_ingreso
                        ),
                        "activo": True,
                    }

                    try:
                        crear_orden_trabajo(datos)

                        st.session_state["mensaje_orden"] = (
                            "Orden de trabajo registrada correctamente."
                        )

                        st.rerun()

                    except Exception as error:
                        st.error(
                            "No fue posible registrar la orden: "
                            f"{error}"
                        )


# =========================================================
# EDITAR ORDEN
# =========================================================

with tab_editar:
    st.subheader("Actualizar orden de trabajo")

    ordenes_edicion = obtener_ordenes_trabajo()

    if not ordenes_edicion:
        st.warning(
            "No existen órdenes disponibles para editar."
        )

    else:
        ordenes_por_id = {
            orden["id"]: orden
            for orden in ordenes_edicion
        }

        orden_id = st.selectbox(
            "Seleccione una orden",
            options=list(ordenes_por_id.keys()),
            format_func=lambda identificador: (
                f'OT-{identificador:05d} | '
                f'{(ordenes_por_id[identificador].get("vehiculos") or {}).get("placa", "")} | '
                f'{ordenes_por_id[identificador].get("estado", "")}'
            ),
        )

        orden = ordenes_por_id[orden_id]

        estado_actual = orden.get("estado", "Abierta")

        indice_estado = (
            ESTADOS_ORDEN.index(estado_actual)
            if estado_actual in ESTADOS_ORDEN
            else 0
        )

        fecha_guardada = orden.get("fecha_estimada_entrega")

        if fecha_guardada:
            fecha_edicion = date.fromisoformat(
                str(fecha_guardada)[:10]
            )
        else:
            fecha_edicion = date.today()

        with st.form(
            f"formulario_editar_orden_{orden_id}"
        ):
            st.info(
                f"Editando la orden OT-{orden_id:05d}"
            )

            columna_1, columna_2 = st.columns(2)

            with columna_1:
                editar_motivo = st.text_area(
                    "Motivo de ingreso *",
                    value=orden.get("motivo_ingreso") or "",
                    height=120,
                )

                editar_kilometraje = st.number_input(
                    "Kilometraje de ingreso",
                    min_value=0,
                    value=int(
                        orden.get("kilometraje_ingreso") or 0
                    ),
                    step=1,
                )

                editar_costo_estimado = st.number_input(
                    "Costo estimado ($)",
                    min_value=0.0,
                    value=float(
                        orden.get("costo_estimado") or 0
                    ),
                    step=1.0,
                    format="%.2f",
                )

            with columna_2:
                editar_diagnostico = st.text_area(
                    "Diagnóstico",
                    value=orden.get("diagnostico") or "",
                    height=120,
                )

                editar_fecha_entrega = st.date_input(
                    "Fecha estimada de entrega",
                    value=fecha_edicion,
                )

                editar_estado = st.selectbox(
                    "Estado",
                    options=ESTADOS_ORDEN,
                    index=indice_estado,
                )

                editar_costo_final = st.number_input(
                    "Costo final ($)",
                    min_value=0.0,
                    value=float(
                        orden.get("costo_final") or 0
                    ),
                    step=1.0,
                    format="%.2f",
                )

            editar_observaciones = st.text_area(
                "Observaciones",
                value=orden.get("observaciones") or "",
            )

            editar_activo = st.checkbox(
                "Orden activa",
                value=orden.get("activo", True),
            )

            actualizar = st.form_submit_button(
                "Actualizar orden de trabajo",
                use_container_width=True,
            )

            if actualizar:
                editar_motivo = editar_motivo.strip()
                editar_diagnostico = editar_diagnostico.strip()
                editar_observaciones = (
                    editar_observaciones.strip()
                )

                if not editar_motivo:
                    st.error(
                        "El motivo de ingreso es obligatorio."
                    )

                else:
                    datos_actualizados = {
                        "motivo_ingreso": editar_motivo,
                        "diagnostico": (
                            editar_diagnostico or None
                        ),
                        "estado": editar_estado,
                        "observaciones": (
                            editar_observaciones or None
                        ),
                        "fecha_estimada_entrega": (
                            editar_fecha_entrega.isoformat()
                        ),
                        "costo_estimado": float(
                            editar_costo_estimado
                        ),
                        "costo_final": float(
                            editar_costo_final
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

                        st.session_state["mensaje_orden"] = (
                            "Orden de trabajo actualizada "
                            "correctamente."
                        )

                        st.rerun()

                    except Exception as error:
                        st.error(
                            "No fue posible actualizar la orden: "
                            f"{error}"
                        )