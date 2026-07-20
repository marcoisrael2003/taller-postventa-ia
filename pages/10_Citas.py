from datetime import date, datetime, time

import pandas as pd
import streamlit as st

from services.supabase_service import (
    actualizar_cita,
    actualizar_estado_cita,
    obtener_citas_completas,
)


# ==========================================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================================

st.set_page_config(
    page_title="Gestión de citas",
    page_icon="📅",
    layout="wide",
)

st.title("📅 Gestión de citas")

st.caption(
    "Planificación, consulta, seguimiento y actualización "
    "de las citas del taller automotriz."
)


# ==========================================================
# CONSTANTES
# ==========================================================

ESTADOS_CITA = [
    "Programada",
    "Confirmada",
    "En atención",
    "Finalizada",
    "Cancelada",
]


# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================

def obtener_valor(registro, *nombres, valor_defecto=None):
    """
    Busca un dato usando diferentes nombres posibles de columna.
    Esto ayuda si la vista de Supabase usa nombres ligeramente distintos.
    """

    for nombre in nombres:
        if nombre in registro:
            valor = registro.get(nombre)

            if valor is not None:
                return valor

    return valor_defecto


def formar_nombre(nombres, apellidos, valor_defecto):
    nombres = str(nombres or "").strip()
    apellidos = str(apellidos or "").strip()

    nombre_completo = f"{nombres} {apellidos}".strip()

    return nombre_completo or valor_defecto


def formar_vehiculo(marca, modelo, anio):
    datos = []

    if marca:
        datos.append(str(marca).strip())

    if modelo:
        datos.append(str(modelo).strip())

    if anio:
        datos.append(str(anio).strip())

    if not datos:
        return "Vehículo no identificado"

    return " ".join(datos)


def crear_codigo_cita(cita_id):
    try:
        return f"CIT-{int(cita_id):05d}"

    except (TypeError, ValueError):
        return "CIT-SIN-CÓDIGO"


def convertir_fecha(valor):
    if valor is None:
        return None

    fecha_convertida = pd.to_datetime(
        valor,
        errors="coerce",
    )

    if pd.isna(fecha_convertida):
        return None

    return fecha_convertida.date()


def convertir_hora(valor):
    if isinstance(valor, time):
        return valor

    if valor is None:
        return time(8, 0)

    texto = str(valor).strip()

    formatos = [
        "%H:%M:%S",
        "%H:%M",
    ]

    for formato in formatos:
        try:
            return datetime.strptime(
                texto,
                formato,
            ).time()

        except ValueError:
            continue

    return time(8, 0)


def mostrar_fecha(valor):
    fecha = convertir_fecha(valor)

    if fecha is None:
        return "Sin fecha"

    return fecha.strftime("%d/%m/%Y")


def mostrar_hora(valor):
    hora = convertir_hora(valor)

    return hora.strftime("%H:%M")


def normalizar_estado(estado):
    estado = str(estado or "").strip()

    equivalencias = {
        "programada": "Programada",
        "confirmada": "Confirmada",
        "en atención": "En atención",
        "en atencion": "En atención",
        "finalizada": "Finalizada",
        "cancelada": "Cancelada",
    }

    return equivalencias.get(
        estado.lower(),
        estado or "Programada",
    )


# ==========================================================
# CARGAR CITAS DESDE SUPABASE
# ==========================================================

try:
    citas = obtener_citas_completas()

except Exception as error:
    st.error(
        "No fue posible cargar las citas desde Supabase."
    )

    st.code(str(error))

    st.info(
        "Revisa que exista la vista "
        "`vista_citas_completa` y que las funciones "
        "del archivo `supabase_service.py` estén guardadas."
    )

    st.stop()


if not citas:
    st.warning(
        "La vista de citas existe, pero todavía no contiene registros."
    )

    st.stop()


# ==========================================================
# CONVERTIR DATOS A DATAFRAME
# ==========================================================

filas = []

for registro in citas:
    cita_id = obtener_valor(
        registro,
        "cita_id",
        "id",
    )

    cliente_nombres = obtener_valor(
        registro,
        "cliente_nombres",
        "nombres_cliente",
        "nombres",
        valor_defecto="",
    )

    cliente_apellidos = obtener_valor(
        registro,
        "cliente_apellidos",
        "apellidos_cliente",
        "apellidos",
        valor_defecto="",
    )

    tecnico_nombres = obtener_valor(
        registro,
        "tecnico_nombres",
        "nombres_tecnico",
        valor_defecto="",
    )

    tecnico_apellidos = obtener_valor(
        registro,
        "tecnico_apellidos",
        "apellidos_tecnico",
        valor_defecto="",
    )

    marca = obtener_valor(
        registro,
        "marca",
        "vehiculo_marca",
    )

    modelo = obtener_valor(
        registro,
        "modelo",
        "vehiculo_modelo",
    )

    anio = obtener_valor(
        registro,
        "anio",
        "vehiculo_anio",
    )

    cliente = formar_nombre(
        cliente_nombres,
        cliente_apellidos,
        "Cliente no identificado",
    )

    tecnico = formar_nombre(
        tecnico_nombres,
        tecnico_apellidos,
        "Sin técnico asignado",
    )

    estado = normalizar_estado(
        obtener_valor(
            registro,
            "estado",
            "estado_cita",
            valor_defecto="Programada",
        )
    )

    fecha_cita = obtener_valor(
        registro,
        "fecha_cita",
        "fecha",
    )

    hora_cita = obtener_valor(
        registro,
        "hora_cita",
        "hora",
    )

    filas.append(
        {
            "Cita ID": cita_id,
            "Código": crear_codigo_cita(cita_id),
            "Fecha": convertir_fecha(fecha_cita),
            "Hora": mostrar_hora(hora_cita),
            "Estado": estado,
            "Cliente": cliente,
            "Cédula": obtener_valor(
                registro,
                "cliente_cedula",
                "cedula_cliente",
                "cedula",
                valor_defecto="No registrada",
            ),
            "Teléfono": obtener_valor(
                registro,
                "cliente_telefono",
                "telefono_cliente",
                "telefono",
                valor_defecto="No registrado",
            ),
            "Correo": obtener_valor(
                registro,
                "cliente_correo",
                "correo_cliente",
                "correo",
                valor_defecto="No registrado",
            ),
            "Placa": obtener_valor(
                registro,
                "placa",
                "vehiculo_placa",
                valor_defecto="Sin placa",
            ),
            "Vehículo": formar_vehiculo(
                marca,
                modelo,
                anio,
            ),
            "Marca": marca or "No registrada",
            "Modelo": modelo or "No registrado",
            "Año": anio or "No registrado",
            "Color": obtener_valor(
                registro,
                "color",
                "vehiculo_color",
                valor_defecto="No registrado",
            ),
            "Técnico": tecnico,
            "Especialidad": obtener_valor(
                registro,
                "tecnico_especialidad",
                "especialidad",
                valor_defecto="No registrada",
            ),
            "Tipo de servicio": obtener_valor(
                registro,
                "tipo_servicio",
                "servicio",
                valor_defecto="No registrado",
            ),
            "Motivo": obtener_valor(
                registro,
                "motivo",
                valor_defecto="No registrado",
            ),
            "Observaciones": obtener_valor(
                registro,
                "observaciones",
                valor_defecto="Sin observaciones",
            ),
            "Registro original": registro,
        }
    )


df = pd.DataFrame(filas)


# ==========================================================
# MÉTRICAS
# ==========================================================

total_citas = len(df)

citas_programadas = int(
    (df["Estado"] == "Programada").sum()
)

citas_confirmadas = int(
    (df["Estado"] == "Confirmada").sum()
)

citas_atencion = int(
    (df["Estado"] == "En atención").sum()
)

citas_finalizadas = int(
    (df["Estado"] == "Finalizada").sum()
)

citas_canceladas = int(
    (df["Estado"] == "Cancelada").sum()
)


col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric(
    "Total",
    total_citas,
)

col2.metric(
    "Programadas",
    citas_programadas,
)

col3.metric(
    "Confirmadas",
    citas_confirmadas,
)

col4.metric(
    "En atención",
    citas_atencion,
)

col5.metric(
    "Finalizadas",
    citas_finalizadas,
)

col6.metric(
    "Canceladas",
    citas_canceladas,
)


st.divider()


# ==========================================================
# FILTROS
# ==========================================================

st.subheader("🔎 Consulta y filtros")

filtro1, filtro2, filtro3, filtro4 = st.columns(4)


with filtro1:
    estados_disponibles = sorted(
        df["Estado"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    estado_filtro = st.selectbox(
        "Estado",
        options=[
            "Todos",
            *estados_disponibles,
        ],
    )


with filtro2:
    tecnicos_disponibles = sorted(
        df["Técnico"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    tecnico_filtro = st.selectbox(
        "Técnico",
        options=[
            "Todos",
            *tecnicos_disponibles,
        ],
    )


with filtro3:
    activar_fecha = st.checkbox(
        "Filtrar por fecha"
    )

    fecha_filtro = st.date_input(
        "Fecha",
        value=date.today(),
        disabled=not activar_fecha,
    )


with filtro4:
    busqueda = st.text_input(
        "Buscar",
        placeholder="Cliente, placa, cédula o servicio",
    )


df_filtrado = df.copy()


if estado_filtro != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["Estado"] == estado_filtro
    ]


if tecnico_filtro != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["Técnico"] == tecnico_filtro
    ]


if activar_fecha:
    df_filtrado = df_filtrado[
        df_filtrado["Fecha"] == fecha_filtro
    ]


if busqueda.strip():
    texto_busqueda = busqueda.strip().lower()

    columnas_busqueda = [
        "Código",
        "Cliente",
        "Cédula",
        "Teléfono",
        "Correo",
        "Placa",
        "Vehículo",
        "Técnico",
        "Especialidad",
        "Tipo de servicio",
        "Motivo",
    ]

    mascara = (
        df_filtrado[columnas_busqueda]
        .astype(str)
        .apply(
            lambda columna: columna.str.lower().str.contains(
                texto_busqueda,
                regex=False,
                na=False,
            )
        )
        .any(axis=1)
    )

    df_filtrado = df_filtrado[mascara]


# ==========================================================
# TABLA PRINCIPAL
# ==========================================================

st.subheader("📋 Listado de citas")

tabla_citas = df_filtrado.copy()

tabla_citas["Fecha"] = tabla_citas["Fecha"].apply(
    lambda valor: (
        valor.strftime("%d/%m/%Y")
        if valor
        else "Sin fecha"
    )
)


st.dataframe(
    tabla_citas[
        [
            "Código",
            "Fecha",
            "Hora",
            "Estado",
            "Cliente",
            "Cédula",
            "Teléfono",
            "Placa",
            "Vehículo",
            "Técnico",
            "Tipo de servicio",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Código": st.column_config.TextColumn(
            "Código",
            width="small",
        ),
        "Estado": st.column_config.TextColumn(
            "Estado",
            width="medium",
        ),
        "Cliente": st.column_config.TextColumn(
            "Cliente",
            width="large",
        ),
        "Vehículo": st.column_config.TextColumn(
            "Vehículo",
            width="large",
        ),
    },
)


st.caption(
    f"Mostrando {len(df_filtrado)} de {len(df)} citas."
)


if df_filtrado.empty:
    st.warning(
        "No existen citas que coincidan con los filtros seleccionados."
    )

    st.stop()


# ==========================================================
# GRÁFICOS
# ==========================================================

st.divider()

st.subheader("📊 Análisis de la agenda")

grafico1, grafico2 = st.columns(2)


with grafico1:
    st.markdown("#### Citas por estado")

    datos_estado = (
        df["Estado"]
        .value_counts()
        .rename_axis("Estado")
        .to_frame("Cantidad")
    )

    st.bar_chart(
        datos_estado,
        use_container_width=True,
    )


with grafico2:
    st.markdown("#### Citas por técnico")

    datos_tecnico = (
        df["Técnico"]
        .value_counts()
        .rename_axis("Técnico")
        .to_frame("Cantidad")
    )

    st.bar_chart(
        datos_tecnico,
        use_container_width=True,
    )


# ==========================================================
# SELECCIÓN DE CITA
# ==========================================================

st.divider()

st.subheader("📝 Detalle y actualización")

opciones_citas = {}


for indice, fila in df_filtrado.iterrows():
    fecha_texto = (
        fila["Fecha"].strftime("%d/%m/%Y")
        if fila["Fecha"]
        else "Sin fecha"
    )

    etiqueta = (
        f"{fila['Código']} | "
        f"{fecha_texto} | "
        f"{fila['Hora']} | "
        f"{fila['Cliente']} | "
        f"{fila['Placa']}"
    )

    opciones_citas[etiqueta] = indice


cita_elegida = st.selectbox(
    "Seleccione una cita",
    options=list(opciones_citas.keys()),
)


indice_cita = opciones_citas[cita_elegida]

fila_cita = df_filtrado.loc[indice_cita]

registro_original = fila_cita["Registro original"]

cita_id = fila_cita["Cita ID"]


if cita_id is None:
    st.error(
        "La cita seleccionada no tiene un identificador válido."
    )

    st.stop()


# ==========================================================
# DETALLE DE CLIENTE, VEHÍCULO Y TÉCNICO
# ==========================================================

detalle1, detalle2, detalle3 = st.columns(3)


with detalle1:
    st.markdown("#### 👤 Cliente")

    st.write(
        f"**Nombre:** {fila_cita['Cliente']}"
    )

    st.write(
        f"**Cédula:** {fila_cita['Cédula']}"
    )

    st.write(
        f"**Teléfono:** {fila_cita['Teléfono']}"
    )

    st.write(
        f"**Correo:** {fila_cita['Correo']}"
    )


with detalle2:
    st.markdown("#### 🚗 Vehículo")

    st.write(
        f"**Placa:** {fila_cita['Placa']}"
    )

    st.write(
        f"**Marca:** {fila_cita['Marca']}"
    )

    st.write(
        f"**Modelo:** {fila_cita['Modelo']}"
    )

    st.write(
        f"**Año:** {fila_cita['Año']}"
    )

    st.write(
        f"**Color:** {fila_cita['Color']}"
    )


with detalle3:
    st.markdown("#### 👨‍🔧 Técnico")

    st.write(
        f"**Nombre:** {fila_cita['Técnico']}"
    )

    st.write(
        f"**Especialidad:** "
        f"{fila_cita['Especialidad']}"
    )

    st.write(
        f"**Estado de la cita:** "
        f"{fila_cita['Estado']}"
    )

    fecha_detalle = (
        fila_cita["Fecha"].strftime("%d/%m/%Y")
        if fila_cita["Fecha"]
        else "Sin fecha"
    )

    st.write(
        f"**Fecha y hora:** "
        f"{fecha_detalle} - {fila_cita['Hora']}"
    )


st.markdown("#### 🔧 Información del servicio")

servicio1, servicio2 = st.columns(2)


with servicio1:
    st.write(
        f"**Tipo de servicio:** "
        f"{fila_cita['Tipo de servicio']}"
    )

    st.write(
        f"**Motivo:** {fila_cita['Motivo']}"
    )


with servicio2:
    st.write(
        f"**Observaciones:** "
        f"{fila_cita['Observaciones']}"
    )


# ==========================================================
# CAMBIO RÁPIDO DE ESTADO
# ==========================================================

st.divider()

st.markdown("#### 🔄 Cambio rápido de estado")

estado_actual = normalizar_estado(
    fila_cita["Estado"]
)

indice_estado = (
    ESTADOS_CITA.index(estado_actual)
    if estado_actual in ESTADOS_CITA
    else 0
)


col_estado1, col_estado2 = st.columns([3, 1])


with col_estado1:
    nuevo_estado_rapido = st.selectbox(
        "Nuevo estado",
        options=ESTADOS_CITA,
        index=indice_estado,
        key=f"estado_rapido_{cita_id}",
    )


with col_estado2:
    st.write("")
    st.write("")

    boton_estado = st.button(
        "Actualizar estado",
        type="primary",
        use_container_width=True,
    )


if boton_estado:
    try:
        actualizar_estado_cita(
            cita_id,
            nuevo_estado_rapido,
        )

        st.success(
            "El estado de la cita fue actualizado correctamente."
        )

        st.rerun()

    except Exception as error:
        st.error(
            "No fue posible actualizar el estado."
        )

        st.code(str(error))


# ==========================================================
# FORMULARIO DE EDICIÓN
# ==========================================================

with st.expander(
    "✏️ Editar información de la cita",
    expanded=False,
):
    fecha_actual = convertir_fecha(
        obtener_valor(
            registro_original,
            "fecha_cita",
            "fecha",
        )
    )

    if fecha_actual is None:
        fecha_actual = date.today()

    hora_actual = convertir_hora(
        obtener_valor(
            registro_original,
            "hora_cita",
            "hora",
        )
    )

    tipo_servicio_actual = str(
        obtener_valor(
            registro_original,
            "tipo_servicio",
            "servicio",
            valor_defecto="",
        )
        or ""
    )

    motivo_actual = str(
        obtener_valor(
            registro_original,
            "motivo",
            valor_defecto="",
        )
        or ""
    )

    observaciones_actuales = str(
        obtener_valor(
            registro_original,
            "observaciones",
            valor_defecto="",
        )
        or ""
    )

    indice_estado_edicion = (
        ESTADOS_CITA.index(estado_actual)
        if estado_actual in ESTADOS_CITA
        else 0
    )

    with st.form(
        key=f"form_editar_cita_{cita_id}"
    ):
        formulario1, formulario2 = st.columns(2)


        with formulario1:
            nueva_fecha = st.date_input(
                "Fecha de la cita",
                value=fecha_actual,
            )

            nueva_hora = st.time_input(
                "Hora de la cita",
                value=hora_actual,
            )

            nuevo_estado = st.selectbox(
                "Estado",
                options=ESTADOS_CITA,
                index=indice_estado_edicion,
                key=f"estado_edicion_{cita_id}",
            )


        with formulario2:
            nuevo_tipo_servicio = st.text_input(
                "Tipo de servicio",
                value=tipo_servicio_actual,
            )

            nuevo_motivo = st.text_area(
                "Motivo de la cita",
                value=motivo_actual,
                height=130,
            )


        nuevas_observaciones = st.text_area(
            "Observaciones",
            value=observaciones_actuales,
            height=130,
        )


        guardar_cambios = st.form_submit_button(
            "Guardar cambios",
            type="primary",
            use_container_width=True,
        )


    if guardar_cambios:
        if not nuevo_tipo_servicio.strip():
            st.error(
                "El tipo de servicio es obligatorio."
            )

        elif nueva_fecha < date.today():
            st.warning(
                "La fecha seleccionada es anterior a la fecha actual. "
                "Puedes guardarla si corresponde a una cita histórica."
            )

            try:
                actualizar_cita(
                    cita_id=cita_id,
                    fecha_cita=nueva_fecha,
                    hora_cita=nueva_hora,
                    tipo_servicio=nuevo_tipo_servicio,
                    motivo=nuevo_motivo,
                    estado=nuevo_estado,
                    observaciones=nuevas_observaciones,
                )

                st.success(
                    "La cita fue actualizada correctamente."
                )

                st.rerun()

            except Exception as error:
                st.error(
                    "No fue posible actualizar la cita."
                )

                st.code(str(error))

        else:
            try:
                actualizar_cita(
                    cita_id=cita_id,
                    fecha_cita=nueva_fecha,
                    hora_cita=nueva_hora,
                    tipo_servicio=nuevo_tipo_servicio,
                    motivo=nuevo_motivo,
                    estado=nuevo_estado,
                    observaciones=nuevas_observaciones,
                )

                st.success(
                    "La cita fue actualizada correctamente."
                )

                st.rerun()

            except Exception as error:
                st.error(
                    "No fue posible actualizar la cita."
                )

                st.code(str(error))