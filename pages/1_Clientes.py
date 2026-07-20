import pandas as pd
import streamlit as st

from services.supabase_service import (
    actualizar_cliente,
    crear_cliente,
    obtener_clientes,
)


st.set_page_config(
    page_title="Clientes",
    page_icon="👥",
    layout="wide",
)

st.title("👥 Gestión de clientes")

if "mensaje_cliente" in st.session_state:
    st.success(st.session_state.pop("mensaje_cliente"))

tab_lista, tab_nuevo, tab_editar = st.tabs(
    [
        "Clientes registrados",
        "Nuevo cliente",
        "Editar cliente",
    ]
)


# ---------------------------------------------------------
# LISTAR CLIENTES
# ---------------------------------------------------------

with tab_lista:
    clientes = obtener_clientes()

    if clientes:
        dataframe = pd.DataFrame(clientes)

        columnas_visibles = [
            "id",
            "cedula",
            "nombres",
            "apellidos",
            "telefono",
            "correo",
            "direccion",
            "fecha_registro",
            "activo",
        ]

        columnas_existentes = [
            columna
            for columna in columnas_visibles
            if columna in dataframe.columns
        ]

        st.dataframe(
            dataframe[columnas_existentes],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("No existen clientes registrados.")


# ---------------------------------------------------------
# CREAR CLIENTE
# ---------------------------------------------------------

with tab_nuevo:
    st.subheader("Registrar cliente")

    with st.form(
        "formulario_cliente",
        clear_on_submit=True,
    ):
        columna_1, columna_2 = st.columns(2)

        with columna_1:
            cedula = st.text_input("Cédula o RUC *")
            nombres = st.text_input("Nombres *")
            telefono = st.text_input("Teléfono")

        with columna_2:
            apellidos = st.text_input("Apellidos *")
            correo = st.text_input("Correo electrónico")
            direccion = st.text_input("Dirección")

        guardar = st.form_submit_button(
            "Guardar cliente",
            use_container_width=True,
        )

        if guardar:
            cedula = cedula.strip()
            nombres = nombres.strip()
            apellidos = apellidos.strip()
            telefono = telefono.strip()
            correo = correo.strip()
            direccion = direccion.strip()

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
                    "direccion": direccion or None,
                    "activo": True,
                }

                try:
                    crear_cliente(datos)

                    st.session_state["mensaje_cliente"] = (
                        "Cliente registrado correctamente."
                    )

                    st.rerun()

                except Exception as error:
                    mensaje = str(error).lower()

                    if (
                        "duplicate key" in mensaje
                        or "clientes_cedula_key" in mensaje
                    ):
                        st.error(
                            "Ya existe un cliente con esa cédula o RUC."
                        )
                    else:
                        st.error(
                            "No fue posible registrar el cliente: "
                            f"{error}"
                        )


# ---------------------------------------------------------
# EDITAR CLIENTE
# ---------------------------------------------------------

with tab_editar:
    st.subheader("Editar información del cliente")

    clientes_edicion = obtener_clientes()

    if not clientes_edicion:
        st.warning(
            "No existen clientes disponibles para editar."
        )
    else:
        clientes_por_id = {
            cliente["id"]: cliente
            for cliente in clientes_edicion
        }

        cliente_id = st.selectbox(
            "Seleccione un cliente",
            options=list(clientes_por_id.keys()),
            format_func=lambda identificador: (
                f'{clientes_por_id[identificador].get("cedula", "")} - '
                f'{clientes_por_id[identificador].get("nombres", "")} '
                f'{clientes_por_id[identificador].get("apellidos", "")}'
            ),
        )

        cliente = clientes_por_id[cliente_id]

        with st.form(
            f"formulario_editar_cliente_{cliente_id}"
        ):
            columna_1, columna_2 = st.columns(2)

            with columna_1:
                editar_cedula = st.text_input(
                    "Cédula o RUC *",
                    value=cliente.get("cedula") or "",
                )

                editar_nombres = st.text_input(
                    "Nombres *",
                    value=cliente.get("nombres") or "",
                )

                editar_telefono = st.text_input(
                    "Teléfono",
                    value=cliente.get("telefono") or "",
                )

            with columna_2:
                editar_apellidos = st.text_input(
                    "Apellidos *",
                    value=cliente.get("apellidos") or "",
                )

                editar_correo = st.text_input(
                    "Correo electrónico",
                    value=cliente.get("correo") or "",
                )

                editar_direccion = st.text_input(
                    "Dirección",
                    value=cliente.get("direccion") or "",
                )

            editar_activo = st.checkbox(
                "Cliente activo",
                value=cliente.get("activo", True),
            )

            actualizar = st.form_submit_button(
                "Actualizar cliente",
                use_container_width=True,
            )

            if actualizar:
                editar_cedula = editar_cedula.strip()
                editar_nombres = editar_nombres.strip()
                editar_apellidos = editar_apellidos.strip()
                editar_telefono = editar_telefono.strip()
                editar_correo = editar_correo.strip()
                editar_direccion = editar_direccion.strip()

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
                        "direccion": editar_direccion or None,
                        "activo": editar_activo,
                    }

                    try:
                        actualizar_cliente(
                            cliente_id,
                            datos_actualizados,
                        )

                        st.session_state["mensaje_cliente"] = (
                            "Cliente actualizado correctamente."
                        )

                        st.rerun()

                    except Exception as error:
                        mensaje = str(error).lower()

                        if (
                            "duplicate key" in mensaje
                            or "clientes_cedula_key" in mensaje
                        ):
                            st.error(
                                "La cédula o RUC ya pertenece "
                                "a otro cliente."
                            )
                        else:
                            st.error(
                                "No fue posible actualizar el cliente: "
                                f"{error}"
                            )