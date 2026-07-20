from datetime import date

import pandas as pd
import streamlit as st

from services.supabase_service import (
    actualizar_tecnico,
    crear_tecnico,
    obtener_tecnicos,
)


st.set_page_config(
    page_title="Técnicos",
    page_icon="👨‍🔧",
    layout="wide",
)

st.title("👨‍🔧 Gestión de técnicos")

NIVELES_TECNICO = [
    "Ayudante",
    "Técnico",
    "Técnico sénior",
    "Jefe de taller",
]

ESPECIALIDADES = [
    "Mecánica general",
    "Electricidad automotriz",
    "Electrónica automotriz",
    "Frenos y suspensión",
    "Motor",
    "Transmisión",
    "Aire acondicionado",
    "Diagnóstico automotriz",
    "Latonería y pintura",
    "Otra",
]

if "mensaje_tecnico" in st.session_state:
    st.success(st.session_state.pop("mensaje_tecnico"))

tab_lista, tab_nuevo, tab_editar = st.tabs(
    [
        "Técnicos registrados",
        "Nuevo técnico",
        "Editar técnico",
    ]
)


# =========================================================
# LISTAR TÉCNICOS
# =========================================================

with tab_lista:
    tecnicos = obtener_tecnicos()

    if tecnicos:
        filas = []

        for tecnico in tecnicos:
            filas.append(
                {
                    "ID": tecnico.get("id"),
                    "Cédula": tecnico.get("cedula"),
                    "Nombres": tecnico.get("nombres"),
                    "Apellidos": tecnico.get("apellidos"),
                    "Teléfono": tecnico.get("telefono"),
                    "Correo": tecnico.get("correo"),
                    "Especialidad": tecnico.get("especialidad"),
                    "Nivel": tecnico.get("nivel"),
                    "Horas diarias": tecnico.get("horas_diarias"),
                    "Costo por hora": tecnico.get("costo_hora"),
                    "Fecha de ingreso": tecnico.get("fecha_ingreso"),
                    "Activo": tecnico.get("activo"),
                }
            )

        dataframe = pd.DataFrame(filas)

        columna_1, columna_2 = st.columns(2)

        with columna_1:
            filtro_estado = st.selectbox(
                "Filtrar por estado",
                options=["Todos", "Activos", "Inactivos"],
            )

        with columna_2:
            busqueda = st.text_input(
                "Buscar por nombre, cédula o especialidad"
            )

        dataframe_filtrado = dataframe.copy()

        if filtro_estado == "Activos":
            dataframe_filtrado = dataframe_filtrado[
                dataframe_filtrado["Activo"] == True
            ]

        elif filtro_estado == "Inactivos":
            dataframe_filtrado = dataframe_filtrado[
                dataframe_filtrado["Activo"] == False
            ]

        if busqueda.strip():
            texto = busqueda.strip().lower()

            mascara = dataframe_filtrado.astype(str).apply(
                lambda fila: fila.str.lower().str.contains(
                    texto,
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
            f"Técnicos mostrados: {len(dataframe_filtrado)}"
        )

    else:
        st.warning("No existen técnicos registrados.")


# =========================================================
# REGISTRAR TÉCNICO
# =========================================================

with tab_nuevo:
    st.subheader("Registrar técnico")

    with st.form(
        "formulario_nuevo_tecnico",
        clear_on_submit=True,
    ):
        columna_1, columna_2 = st.columns(2)

        with columna_1:
            cedula = st.text_input("Cédula *")
            nombres = st.text_input("Nombres *")
            telefono = st.text_input("Teléfono")

            especialidad = st.selectbox(
                "Especialidad *",
                options=ESPECIALIDADES,
            )

            horas_diarias = st.number_input(
                "Horas de trabajo diarias",
                min_value=1.0,
                max_value=24.0,
                value=8.0,
                step=0.5,
            )

        with columna_2:
            apellidos = st.text_input("Apellidos *")
            correo = st.text_input("Correo electrónico")

            nivel = st.selectbox(
                "Nivel *",
                options=NIVELES_TECNICO,
                index=1,
            )

            costo_hora = st.number_input(
                "Costo por hora ($)",
                min_value=0.0,
                value=0.0,
                step=0.50,
                format="%.2f",
            )

            fecha_ingreso = st.date_input(
                "Fecha de ingreso",
                value=date.today(),
            )

        guardar = st.form_submit_button(
            "Guardar técnico",
            use_container_width=True,
        )

        if guardar:
            cedula = cedula.strip()
            nombres = nombres.strip()
            apellidos = apellidos.strip()
            telefono = telefono.strip()
            correo = correo.strip()

            if not cedula or not nombres or not apellidos:
                st.error(
                    "Cédula, nombres y apellidos son obligatorios."
                )

            else:
                datos = {
                    "cedula": cedula,
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "telefono": telefono or None,
                    "correo": correo or None,
                    "especialidad": especialidad,
                    "nivel": nivel,
                    "horas_diarias": float(horas_diarias),
                    "costo_hora": float(costo_hora),
                    "fecha_ingreso": fecha_ingreso.isoformat(),
                    "activo": True,
                }

                try:
                    crear_tecnico(datos)

                    st.session_state["mensaje_tecnico"] = (
                        "Técnico registrado correctamente."
                    )

                    st.rerun()

                except Exception as error:
                    mensaje = str(error).lower()

                    if (
                        "duplicate key" in mensaje
                        or "tecnicos_cedula_key" in mensaje
                    ):
                        st.error(
                            "Ya existe un técnico con esa cédula."
                        )
                    else:
                        st.error(
                            "No fue posible registrar el técnico: "
                            f"{error}"
                        )


# =========================================================
# EDITAR TÉCNICO
# =========================================================

with tab_editar:
    st.subheader("Editar información del técnico")

    tecnicos_edicion = obtener_tecnicos()

    if not tecnicos_edicion:
        st.warning(
            "No existen técnicos disponibles para editar."
        )

    else:
        tecnicos_por_id = {
            tecnico["id"]: tecnico
            for tecnico in tecnicos_edicion
        }

        tecnico_id = st.selectbox(
            "Seleccione un técnico",
            options=list(tecnicos_por_id.keys()),
            format_func=lambda identificador: (
                f'{tecnicos_por_id[identificador].get("cedula", "")} - '
                f'{tecnicos_por_id[identificador].get("nombres", "")} '
                f'{tecnicos_por_id[identificador].get("apellidos", "")}'
            ),
        )

        tecnico = tecnicos_por_id[tecnico_id]

        nivel_actual = tecnico.get("nivel", "Técnico")
        especialidad_actual = tecnico.get(
            "especialidad",
            "Mecánica general",
        )

        indice_nivel = (
            NIVELES_TECNICO.index(nivel_actual)
            if nivel_actual in NIVELES_TECNICO
            else 1
        )

        indice_especialidad = (
            ESPECIALIDADES.index(especialidad_actual)
            if especialidad_actual in ESPECIALIDADES
            else len(ESPECIALIDADES) - 1
        )

        fecha_guardada = tecnico.get("fecha_ingreso")

        if fecha_guardada:
            fecha_edicion = date.fromisoformat(
                str(fecha_guardada)[:10]
            )
        else:
            fecha_edicion = date.today()

        with st.form(
            f"formulario_editar_tecnico_{tecnico_id}"
        ):
            columna_1, columna_2 = st.columns(2)

            with columna_1:
                editar_cedula = st.text_input(
                    "Cédula *",
                    value=tecnico.get("cedula") or "",
                )

                editar_nombres = st.text_input(
                    "Nombres *",
                    value=tecnico.get("nombres") or "",
                )

                editar_telefono = st.text_input(
                    "Teléfono",
                    value=tecnico.get("telefono") or "",
                )

                editar_especialidad = st.selectbox(
                    "Especialidad *",
                    options=ESPECIALIDADES,
                    index=indice_especialidad,
                )

                editar_horas = st.number_input(
                    "Horas de trabajo diarias",
                    min_value=1.0,
                    max_value=24.0,
                    value=float(
                        tecnico.get("horas_diarias") or 8
                    ),
                    step=0.5,
                )

            with columna_2:
                editar_apellidos = st.text_input(
                    "Apellidos *",
                    value=tecnico.get("apellidos") or "",
                )

                editar_correo = st.text_input(
                    "Correo electrónico",
                    value=tecnico.get("correo") or "",
                )

                editar_nivel = st.selectbox(
                    "Nivel *",
                    options=NIVELES_TECNICO,
                    index=indice_nivel,
                )

                editar_costo_hora = st.number_input(
                    "Costo por hora ($)",
                    min_value=0.0,
                    value=float(
                        tecnico.get("costo_hora") or 0
                    ),
                    step=0.50,
                    format="%.2f",
                )

                editar_fecha_ingreso = st.date_input(
                    "Fecha de ingreso",
                    value=fecha_edicion,
                )

            editar_activo = st.checkbox(
                "Técnico activo",
                value=tecnico.get("activo", True),
            )

            actualizar = st.form_submit_button(
                "Actualizar técnico",
                use_container_width=True,
            )

            if actualizar:
                editar_cedula = editar_cedula.strip()
                editar_nombres = editar_nombres.strip()
                editar_apellidos = editar_apellidos.strip()
                editar_telefono = editar_telefono.strip()
                editar_correo = editar_correo.strip()

                if (
                    not editar_cedula
                    or not editar_nombres
                    or not editar_apellidos
                ):
                    st.error(
                        "Cédula, nombres y apellidos son obligatorios."
                    )

                else:
                    datos_actualizados = {
                        "cedula": editar_cedula,
                        "nombres": editar_nombres,
                        "apellidos": editar_apellidos,
                        "telefono": editar_telefono or None,
                        "correo": editar_correo or None,
                        "especialidad": editar_especialidad,
                        "nivel": editar_nivel,
                        "horas_diarias": float(editar_horas),
                        "costo_hora": float(
                            editar_costo_hora
                        ),
                        "fecha_ingreso": (
                            editar_fecha_ingreso.isoformat()
                        ),
                        "activo": editar_activo,
                    }

                    try:
                        actualizar_tecnico(
                            tecnico_id,
                            datos_actualizados,
                        )

                        st.session_state["mensaje_tecnico"] = (
                            "Técnico actualizado correctamente."
                        )

                        st.rerun()

                    except Exception as error:
                        mensaje = str(error).lower()

                        if (
                            "duplicate key" in mensaje
                            or "tecnicos_cedula_key" in mensaje
                        ):
                            st.error(
                                "La cédula ya pertenece "
                                "a otro técnico."
                            )
                        else:
                            st.error(
                                "No fue posible actualizar el técnico: "
                                f"{error}"
                            )