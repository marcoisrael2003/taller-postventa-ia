import re
from collections import Counter
from datetime import date, timedelta

import streamlit as st
from openai import OpenAI
from supabase import create_client


# =========================================================
# CONFIGURACIÓN DE LA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Asistente IA",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Asistente Inteligente del Taller")

st.write(
    "Consulta información registrada en el taller o realiza preguntas "
    "sobre mantenimiento y diagnóstico automotriz."
)

st.info(
    "Ejemplos: ¿Cuántos clientes hay?, ¿quién es el técnico con más "
    "órdenes?, ¿qué citas hay registradas?, ¿qué significa el código P0300?"
)


# =========================================================
# CONEXIONES
# =========================================================

try:
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )

    cliente_ia = OpenAI(
        api_key=st.secrets["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": (
                "https://asistente-ia-mantenimiento-automotriz.streamlit.app"
            ),
            "X-OpenRouter-Title": "Taller Postventa IA",
        },
    )

except KeyError as error:
    st.error(f"Falta configurar un secreto en Streamlit: {error}")
    st.stop()

except Exception as error:
    st.error(f"No fue posible iniciar las conexiones: {error}")
    st.stop()


# =========================================================
# FUNCIONES GENERALES DE SUPABASE
# =========================================================

def consultar_tabla(nombre_tabla: str, limite: int = 500) -> list:
    """
    Consulta una tabla de Supabase.
    Si la tabla no existe, devuelve una lista vacía.
    """
    try:
        respuesta = (
            supabase
            .table(nombre_tabla)
            .select("*")
            .limit(limite)
            .execute()
        )

        return respuesta.data or []

    except Exception:
        return []


def primer_valor(registro: dict, campos: list, valor_defecto="No registrado"):
    """
    Obtiene el primer campo disponible dentro de un registro.
    """
    for campo in campos:
        valor = registro.get(campo)

        if valor is not None and str(valor).strip():
            return valor

    return valor_defecto


def normalizar_texto(texto: str) -> str:
    return (
        texto.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )


def construir_nombre(registro: dict) -> str:
    nombre_completo = primer_valor(
        registro,
        [
            "nombre_completo",
            "nombres_completos",
            "nombre",
            "tecnico",
            "cliente",
        ],
        "",
    )

    apellido = primer_valor(
        registro,
        [
            "apellido",
            "apellidos",
        ],
        "",
    )

    nombre_final = f"{nombre_completo} {apellido}".strip()

    if nombre_final:
        return nombre_final

    return "Sin nombre"


# =========================================================
# CARGA DE DATOS
# =========================================================

@st.cache_data(ttl=30)
def cargar_datos_taller():
    return {
        "clientes": consultar_tabla("clientes"),
        "vehiculos": consultar_tabla("vehiculos"),
        "tecnicos": consultar_tabla("tecnicos"),
        "ordenes": consultar_tabla("ordenes_trabajo"),
        "citas": consultar_tabla("citas"),
        "asignaciones": consultar_tabla("asignaciones_tecnicos"),
        "servicios": consultar_tabla("servicios_orden"),
        "repuestos": consultar_tabla("repuestos_orden"),
    }


# =========================================================
# FUNCIONES DE BÚSQUEDA
# =========================================================

def obtener_id(registro: dict):
    return primer_valor(
        registro,
        [
            "id",
            "tecnico_id",
            "cliente_id",
            "vehiculo_id",
            "orden_id",
            "id_tecnico",
            "id_cliente",
            "id_vehiculo",
            "id_orden",
        ],
        None,
    )


def obtener_tecnico_id_desde_orden(orden: dict):
    return primer_valor(
        orden,
        [
            "tecnico_id",
            "id_tecnico",
            "tecnico_asignado_id",
            "responsable_id",
        ],
        None,
    )


def obtener_orden_id_desde_asignacion(asignacion: dict):
    return primer_valor(
        asignacion,
        [
            "orden_id",
            "id_orden",
            "orden_trabajo_id",
        ],
        None,
    )


def obtener_tecnico_id_desde_asignacion(asignacion: dict):
    return primer_valor(
        asignacion,
        [
            "tecnico_id",
            "id_tecnico",
        ],
        None,
    )


def respuesta_cantidad(datos: dict, pregunta: str):
    texto = normalizar_texto(pregunta)

    tablas = {
        "cliente": ("clientes", "clientes"),
        "vehiculo": ("vehiculos", "vehículos"),
        "tecnico": ("tecnicos", "técnicos"),
        "orden": ("ordenes", "órdenes de trabajo"),
        "cita": ("citas", "citas"),
    }

    if not any(
        expresion in texto
        for expresion in [
            "cuantos",
            "cuantas",
            "cantidad",
            "numero de",
            "total de",
        ]
    ):
        return None

    for palabra, (clave, etiqueta) in tablas.items():
        if palabra in texto:
            cantidad = len(datos[clave])

            return (
                f"Actualmente existen **{cantidad} {etiqueta}** "
                f"registrados en la base de datos del taller."
            )

    return None


def respuesta_tecnicos(datos: dict, pregunta: str):
    texto = normalizar_texto(pregunta)
    tecnicos = datos["tecnicos"]
    ordenes = datos["ordenes"]
    asignaciones = datos["asignaciones"]

    if "tecnico" not in texto:
        return None

    if not tecnicos:
        return (
            "No fue posible encontrar técnicos registrados en la tabla "
            "`tecnicos` de Supabase."
        )

    # -----------------------------------------------------
    # Técnico con mayor cantidad de órdenes
    # -----------------------------------------------------

    if (
        "mas orden" in texto
        or "mayor carga" in texto
        or "mas trabajo" in texto
        or "mayor numero de orden" in texto
    ):
        conteo = Counter()

        # Primero se intenta contar desde la tabla de asignaciones.
        for asignacion in asignaciones:
            tecnico_id = obtener_tecnico_id_desde_asignacion(asignacion)

            if tecnico_id is not None:
                conteo[str(tecnico_id)] += 1

        # Si no existe tabla de asignaciones, se cuenta desde órdenes.
        if not conteo:
            for orden in ordenes:
                tecnico_id = obtener_tecnico_id_desde_orden(orden)

                if tecnico_id is not None:
                    conteo[str(tecnico_id)] += 1

        if not conteo:
            return (
                "Los técnicos están registrados, pero no encontré una "
                "relación de asignación entre técnicos y órdenes. Revisa "
                "si la tabla utiliza `tecnico_id`, `id_tecnico` o una tabla "
                "de asignaciones."
            )

        tecnico_id, cantidad = conteo.most_common(1)[0]

        tecnico_encontrado = None

        for tecnico in tecnicos:
            identificador = primer_valor(
                tecnico,
                ["id", "tecnico_id", "id_tecnico"],
                None,
            )

            if identificador is not None and str(identificador) == tecnico_id:
                tecnico_encontrado = tecnico
                break

        if tecnico_encontrado:
            nombre = construir_nombre(tecnico_encontrado)

            especialidad = primer_valor(
                tecnico_encontrado,
                [
                    "especialidad",
                    "area",
                    "especializacion",
                ],
            )

            return (
                f"El técnico con más órdenes asignadas es "
                f"**{nombre}**, con **{cantidad} órdenes de trabajo**. "
                f"Su especialidad registrada es **{especialidad}**."
            )

        return (
            f"El técnico identificado con el código **{tecnico_id}** "
            f"tiene la mayor carga, con **{cantidad} órdenes asignadas**."
        )

    # -----------------------------------------------------
    # Lista de técnicos
    # -----------------------------------------------------

    if (
        "que tecnicos" in texto
        or "lista de tecnicos" in texto
        or "tecnicos trabajan" in texto
        or "mostrar tecnicos" in texto
    ):
        lineas = []

        for tecnico in tecnicos[:20]:
            nombre = construir_nombre(tecnico)

            especialidad = primer_valor(
                tecnico,
                [
                    "especialidad",
                    "area",
                    "especializacion",
                ],
            )

            estado = primer_valor(
                tecnico,
                [
                    "estado",
                    "disponibilidad",
                    "activo",
                ],
            )

            lineas.append(
                f"- **{nombre}** — Especialidad: {especialidad}; "
                f"Estado: {estado}."
            )

        return (
            f"Se encontraron **{len(tecnicos)} técnicos** registrados:\n\n"
            + "\n".join(lineas)
        )

    # -----------------------------------------------------
    # Búsqueda por nombre
    # -----------------------------------------------------

    for tecnico in tecnicos:
        nombre = construir_nombre(tecnico)

        if normalizar_texto(nombre) in texto:
            especialidad = primer_valor(
                tecnico,
                ["especialidad", "area", "especializacion"],
            )

            cargo = primer_valor(
                tecnico,
                ["cargo", "puesto"],
            )

            estado = primer_valor(
                tecnico,
                ["estado", "disponibilidad", "activo"],
            )

            return (
                f"Información registrada de **{nombre}**:\n\n"
                f"- Cargo: **{cargo}**\n"
                f"- Especialidad: **{especialidad}**\n"
                f"- Estado o disponibilidad: **{estado}**"
            )

    return None


def respuesta_ordenes(datos: dict, pregunta: str):
    texto = normalizar_texto(pregunta)
    ordenes = datos["ordenes"]

    if "orden" not in texto:
        return None

    if not ordenes:
        return "No existen órdenes de trabajo registradas."

    if "abierta" in texto or "pendiente" in texto or "proceso" in texto:
        estados_buscados = []

        if "abierta" in texto:
            estados_buscados.append("abierta")

        if "pendiente" in texto:
            estados_buscados.append("pendiente")

        if "proceso" in texto:
            estados_buscados.extend(
                ["proceso", "en proceso"]
            )

        encontradas = []

        for orden in ordenes:
            estado = normalizar_texto(
                str(
                    primer_valor(
                        orden,
                        ["estado", "estatus"],
                        "",
                    )
                )
            )

            if any(valor in estado for valor in estados_buscados):
                encontradas.append(orden)

        return (
            f"Se encontraron **{len(encontradas)} órdenes** con el "
            f"estado solicitado."
        )

    return None


def respuesta_citas(datos: dict, pregunta: str):
    texto = normalizar_texto(pregunta)
    citas = datos["citas"]

    if "cita" not in texto:
        return None

    if not citas:
        return "No existen citas registradas en la base de datos."

    if "manana" in texto:
        fecha_buscada = date.today() + timedelta(days=1)
    elif "hoy" in texto:
        fecha_buscada = date.today()
    else:
        fecha_buscada = None

    if fecha_buscada:
        citas_encontradas = []

        for cita in citas:
            fecha = str(
                primer_valor(
                    cita,
                    [
                        "fecha",
                        "fecha_cita",
                        "fecha_hora",
                        "inicio",
                    ],
                    "",
                )
            )

            if fecha.startswith(str(fecha_buscada)):
                citas_encontradas.append(cita)

        if not citas_encontradas:
            return (
                f"No existen citas registradas para el "
                f"**{fecha_buscada.strftime('%d/%m/%Y')}**."
            )

        lineas = []

        for cita in citas_encontradas:
            hora = primer_valor(
                cita,
                ["hora", "hora_cita", "fecha_hora"],
            )

            motivo = primer_valor(
                cita,
                ["motivo", "servicio", "descripcion", "observaciones"],
            )

            estado = primer_valor(
                cita,
                ["estado", "estatus"],
            )

            lineas.append(
                f"- Hora: **{hora}** — Motivo: {motivo} — Estado: {estado}"
            )

        return (
            f"Existen **{len(citas_encontradas)} citas** para el "
            f"**{fecha_buscada.strftime('%d/%m/%Y')}**:\n\n"
            + "\n".join(lineas)
        )

    return (
        f"Actualmente existen **{len(citas)} citas** registradas "
        f"en la base de datos."
    )


def respuesta_vehiculos(datos: dict, pregunta: str):
    texto = normalizar_texto(pregunta)
    vehiculos = datos["vehiculos"]

    if "vehiculo" not in texto and "placa" not in texto:
        return None

    # Busca una placa aproximada en la pregunta.
    patron_placa = re.search(
        r"\b[A-Z]{2,3}[-\s]?\d{3,4}\b",
        pregunta.upper(),
    )

    if patron_placa:
        placa_buscada = (
            patron_placa.group(0)
            .replace(" ", "")
            .replace("-", "")
        )

        for vehiculo in vehiculos:
            placa = str(
                primer_valor(
                    vehiculo,
                    ["placa", "matricula"],
                    "",
                )
            )

            placa_normalizada = placa.replace(" ", "").replace("-", "").upper()

            if placa_normalizada == placa_buscada:
                marca = primer_valor(vehiculo, ["marca"])
                modelo = primer_valor(vehiculo, ["modelo"])
                anio = primer_valor(vehiculo, ["anio", "año"])
                kilometraje = primer_valor(
                    vehiculo,
                    ["kilometraje", "km"],
                )

                return (
                    f"El vehículo con placa **{placa}** corresponde a:\n\n"
                    f"- Marca: **{marca}**\n"
                    f"- Modelo: **{modelo}**\n"
                    f"- Año: **{anio}**\n"
                    f"- Kilometraje: **{kilometraje} km**"
                )

        return f"No se encontró un vehículo con la placa **{patron_placa.group(0)}**."

    return None


# =========================================================
# DETECTOR DE CONSULTAS DE BASE DE DATOS
# =========================================================

def consultar_base_de_datos(pregunta: str):
    datos = cargar_datos_taller()

    funciones = [
        respuesta_cantidad,
        respuesta_tecnicos,
        respuesta_ordenes,
        respuesta_citas,
        respuesta_vehiculos,
    ]

    for funcion in funciones:
        respuesta = funcion(datos, pregunta)

        if respuesta:
            return respuesta

    return None


# =========================================================
# CONSULTA TÉCNICA A OPENROUTER
# =========================================================

INSTRUCCIONES_IA = """
Eres el asistente técnico virtual del taller automotriz Doctor Fierros.

Responde siempre en español, con lenguaje profesional y claro.

Puedes ayudar con mantenimiento preventivo, diagnóstico inicial,
códigos OBD-II, frenos, suspensión, motor, transmisión, electricidad
automotriz, órdenes de trabajo y atención al cliente.

Cuando se describa una falla, responde con:

1. Resumen del problema.
2. Posibles causas.
3. Pruebas recomendadas.
4. Nivel de urgencia.
5. Recomendación final.

No confirmes una avería sin inspección y pruebas técnicas.
No inventes información de la base de datos del taller.
"""


def consultar_ia_tecnica(pregunta: str, historial: list) -> str:
    mensajes = [
        {
            "role": "system",
            "content": INSTRUCCIONES_IA,
        }
    ]

    mensajes.extend(historial[-10:])
    mensajes.append({"role": "user", "content": pregunta})

    try:
        respuesta = cliente_ia.chat.completions.create(
            model="openrouter/free",
            messages=mensajes,
            temperature=0.3,
            max_tokens=800,
        )

        texto = respuesta.choices[0].message.content

        return texto or "El modelo no produjo una respuesta."

    except Exception as error:
        detalle = str(error)

        if "429" in detalle:
            return (
                "El modelo gratuito alcanzó temporalmente su límite. "
                "Espera unos minutos e intenta nuevamente."
            )

        if "401" in detalle:
            return (
                "La clave de OpenRouter no es válida o no está "
                "configurada correctamente."
            )

        return f"No fue posible consultar la IA. Detalle: {detalle}"


# =========================================================
# INTERFAZ DEL CHAT
# =========================================================

if "historial_ia" not in st.session_state:
    st.session_state.historial_ia = [
        {
            "role": "assistant",
            "content": (
                "Hola. Puedo consultar información del taller almacenada "
                "en Supabase y responder preguntas técnicas automotrices."
            ),
        }
    ]


col1, col2 = st.columns([5, 1])

with col2:
    if st.button("🗑️ Limpiar chat", use_container_width=True):
        st.session_state.historial_ia = [
            {
                "role": "assistant",
                "content": "La conversación fue reiniciada.",
            }
        ]

        st.rerun()


with st.expander("💡 Preguntas para probar"):
    st.markdown(
        """
        - ¿Cuántos clientes hay registrados?
        - ¿Cuántos vehículos existen?
        - ¿Quién es el técnico con más órdenes de trabajo asignadas?
        - ¿Qué técnicos trabajan en el taller?
        - ¿Cuántas órdenes están pendientes?
        - ¿Qué citas existen para mañana?
        - ¿Qué información existe del vehículo con placa ABC-1234?
        - ¿Qué significa el código P0300?
        - ¿Qué se debe revisar si un vehículo vibra al frenar?
        """
    )


for mensaje in st.session_state.historial_ia:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])


pregunta = st.chat_input(
    "Escribe una consulta sobre el taller o sobre mecánica automotriz..."
)


if pregunta:
    with st.chat_message("user"):
        st.markdown(pregunta)

    historial_anterior = st.session_state.historial_ia.copy()

    st.session_state.historial_ia.append(
        {
            "role": "user",
            "content": pregunta,
        }
    )

    with st.chat_message("assistant"):
        with st.spinner("Consultando información..."):
            respuesta_bd = consultar_base_de_datos(pregunta)

            if respuesta_bd:
                respuesta_final = respuesta_bd
            else:
                respuesta_final = consultar_ia_tecnica(
                    pregunta,
                    historial_anterior,
                )

        st.markdown(respuesta_final)

    st.session_state.historial_ia.append(
        {
            "role": "assistant",
            "content": respuesta_final,
        }
    )