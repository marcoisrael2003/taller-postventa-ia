import pandas as pd
import streamlit as st

from services.supabase_service import (
    actualizar_vehiculo,
    crear_vehiculo,
    obtener_clientes,
    obtener_vehiculos,
)


st.set_page_config(
    page_title="Vehículos",
    page_icon="🚗",
    layout="wide",
)

st.title("🚗 Gestión de vehículos")

if "mensaje_vehiculo" in st.session_state:
    st.success(st.session_state.pop("mensaje_vehiculo"))

tab_lista, tab_nuevo, tab_editar = st.tabs(
    [
        "Vehículos registrados",
        "Nuevo vehículo",
        "Editar vehículo",
    ]
)


# ---------------------------------------------------------
# LISTAR VEHÍCULOS
# ---------------------------------------------------------

with tab_lista:
    vehiculos = obtener_vehiculos()

    if vehiculos:
        filas = []

        for vehiculo in vehiculos:
            cliente = vehiculo.get("clientes") or {}

            filas.append(
                {
                    "ID": vehiculo.get("id"),
                    "Placa": vehiculo.get("placa"),
                    "Marca": vehiculo.get("marca"),
                    "Modelo": vehiculo.get("modelo"),
                    "Año": vehiculo.get("anio"),
                    "Color": vehiculo.get("color"),
                    "Kilometraje": vehiculo.get("kilometraje"),
                    "VIN": vehiculo.get("vin"),
                    "Propietario": (
                        f'{cliente.get("nombres", "")} '
                        f'{cliente.get("apellidos", "")}'
                    ).strip(),
                    "Cédula": cliente.get("cedula"),
                    "Activo": vehiculo.get("activo"),
                    "Fecha de registro": vehiculo.get("fecha_registro"),
                }
            )

        dataframe = pd.DataFrame(filas)

        st.dataframe(
            dataframe,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("No existen vehículos registrados.")


# ---------------------------------------------------------
# CREAR VEHÍCULO
# ---------------------------------------------------------

with tab_nuevo:
    st.subheader("Registrar vehículo")

    clientes = obtener_clientes()
    clientes_activos = [
        cliente
        for cliente in clientes
        if cliente.get("activo", True)
    ]

    if not clientes_activos:
        st.warning(
            "Primero debes registrar al menos un cliente activo."
        )
    else:
        clientes_por_id = {
            cliente["id"]: cliente
            for cliente in clientes_activos
        }

        with st.form(
            "formulario_vehiculo",
            clear_on_submit=True,
        ):
            cliente_id = st.selectbox(
                "Propietario *",
                options=list(clientes_por_id.keys()),
                format_func=lambda identificador: (
                    f'{clientes_por_id[identificador].get("cedula", "")} - '
                    f'{clientes_por_id[identificador].get("nombres", "")} '
                    f'{clientes_por_id[identificador].get("apellidos", "")}'
                ),
            )

            columna_1, columna_2 = st.columns(2)

            with columna_1:
                placa = st.text_input("Placa *")
                marca = st.text_input("Marca *")
                anio = st.number_input(
                    "Año",
                    min_value=1900,
                    max_value=2100,
                    value=2025,
                    step=1,
                )
                kilometraje = st.number_input(
                    "Kilometraje",
                    min_value=0,
                    value=0,
                    step=1,
                )

            with columna_2:
                modelo = st.text_input("Modelo *")
                color = st.text_input("Color")
                vin = st.text_input("VIN o número de chasis")

            guardar = st.form_submit_button(
                "Guardar vehículo",
                use_container_width=True,
            )

            if guardar:
                placa = placa.strip().upper()
                marca = marca.strip()
                modelo = modelo.strip()
                color = color.strip()
                vin = vin.strip().upper()

                if not placa or not marca or not modelo:
                    st.error(
                        "Placa, marca y modelo son obligatorios."
                    )
                else:
                    datos = {
                        "cliente_id": cliente_id,
                        "placa": placa,
                        "marca": marca,
                        "modelo": modelo,
                        "anio": int(anio),
                        "color": color or None,
                        "kilometraje": int(kilometraje),
                        "vin": vin or None,
                        "activo": True,
                    }

                    try:
                        crear_vehiculo(datos)

                        st.session_state["mensaje_vehiculo"] = (
                            "Vehículo registrado correctamente."
                        )

                        st.rerun()

                    except Exception as error:
                        mensaje = str(error).lower()

                        if (
                            "duplicate key" in mensaje
                            or "vehiculos_placa_key" in mensaje
                        ):
                            st.error(
                                "Ya existe un vehículo con esa placa."
                            )
                        else:
                            st.error(
                                "No fue posible registrar el vehículo: "
                                f"{error}"
                            )


# ---------------------------------------------------------
# EDITAR VEHÍCULO
# ---------------------------------------------------------

with tab_editar:
    st.subheader("Editar información del vehículo")

    vehiculos_edicion = obtener_vehiculos()
    clientes_edicion = obtener_clientes()

    if not vehiculos_edicion:
        st.warning(
            "No existen vehículos disponibles para editar."
        )
    elif not clientes_edicion:
        st.warning(
            "No existen clientes disponibles."
        )
    else:
        vehiculos_por_id = {
            vehiculo["id"]: vehiculo
            for vehiculo in vehiculos_edicion
        }

        clientes_por_id = {
            cliente["id"]: cliente
            for cliente in clientes_edicion
        }

        vehiculo_id = st.selectbox(
            "Seleccione un vehículo",
            options=list(vehiculos_por_id.keys()),
            format_func=lambda identificador: (
                f'{vehiculos_por_id[identificador].get("placa", "")} - '
                f'{vehiculos_por_id[identificador].get("marca", "")} '
                f'{vehiculos_por_id[identificador].get("modelo", "")}'
            ),
        )

        vehiculo = vehiculos_por_id[vehiculo_id]

        ids_clientes = list(clientes_por_id.keys())
        cliente_actual = vehiculo.get("cliente_id")

        indice_cliente = (
            ids_clientes.index(cliente_actual)
            if cliente_actual in ids_clientes
            else 0
        )

        with st.form(
            f"formulario_editar_vehiculo_{vehiculo_id}"
        ):
            editar_cliente_id = st.selectbox(
                "Propietario *",
                options=ids_clientes,
                index=indice_cliente,
                format_func=lambda identificador: (
                    f'{clientes_por_id[identificador].get("cedula", "")} - '
                    f'{clientes_por_id[identificador].get("nombres", "")} '
                    f'{clientes_por_id[identificador].get("apellidos", "")}'
                ),
            )

            columna_1, columna_2 = st.columns(2)

            with columna_1:
                editar_placa = st.text_input(
                    "Placa *",
                    value=vehiculo.get("placa") or "",
                )

                editar_marca = st.text_input(
                    "Marca *",
                    value=vehiculo.get("marca") or "",
                )

                editar_anio = st.number_input(
                    "Año",
                    min_value=1900,
                    max_value=2100,
                    value=int(vehiculo.get("anio") or 2025),
                    step=1,
                )

                editar_kilometraje = st.number_input(
                    "Kilometraje",
                    min_value=0,
                    value=int(
                        vehiculo.get("kilometraje") or 0
                    ),
                    step=1,
                )

            with columna_2:
                editar_modelo = st.text_input(
                    "Modelo *",
                    value=vehiculo.get("modelo") or "",
                )

                editar_color = st.text_input(
                    "Color",
                    value=vehiculo.get("color") or "",
                )

                editar_vin = st.text_input(
                    "VIN o número de chasis",
                    value=vehiculo.get("vin") or "",
                )

            editar_activo = st.checkbox(
                "Vehículo activo",
                value=vehiculo.get("activo", True),
            )

            actualizar = st.form_submit_button(
                "Actualizar vehículo",
                use_container_width=True,
            )

            if actualizar:
                editar_placa = editar_placa.strip().upper()
                editar_marca = editar_marca.strip()
                editar_modelo = editar_modelo.strip()
                editar_color = editar_color.strip()
                editar_vin = editar_vin.strip().upper()

                if (
                    not editar_placa
                    or not editar_marca
                    or not editar_modelo
                ):
                    st.error(
                        "Placa, marca y modelo son obligatorios."
                    )
                else:
                    datos_actualizados = {
                        "cliente_id": editar_cliente_id,
                        "placa": editar_placa,
                        "marca": editar_marca,
                        "modelo": editar_modelo,
                        "anio": int(editar_anio),
                        "color": editar_color or None,
                        "kilometraje": int(editar_kilometraje),
                        "vin": editar_vin or None,
                        "activo": editar_activo,
                    }

                    try:
                        actualizar_vehiculo(
                            vehiculo_id,
                            datos_actualizados,
                        )

                        st.session_state["mensaje_vehiculo"] = (
                            "Vehículo actualizado correctamente."
                        )

                        st.rerun()

                    except Exception as error:
                        mensaje = str(error).lower()

                        if (
                            "duplicate key" in mensaje
                            or "vehiculos_placa_key" in mensaje
                        ):
                            st.error(
                                "La placa ya pertenece "
                                "a otro vehículo."
                            )
                        else:
                            st.error(
                                "No fue posible actualizar el vehículo: "
                                f"{error}"
                            )