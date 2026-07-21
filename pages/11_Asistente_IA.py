from collections import Counter
from datetime import date, timedelta
import re
import unicodedata

import streamlit as st
from openai import OpenAI
from supabase import create_client

from services.supabase_service import (
    obtener_ordenes_trabajo,
    obtener_tecnicos,
    obtener_vehiculos,
)


# =========================================================
# CONFIGURACIÓN DE LA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Asistente IA",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Asistente Inteligente del Taller")

st.caption(
    "Consulta información almacenada en Supabase o realiza "
    "preguntas técnicas sobre mantenimiento automotriz."
)

st.info(
    "Ejemplos: ¿Quién tiene más órdenes?, ¿cuántos técnicos hay?, "
    "¿qué citas existen?, ¿qué significa el código P0300?"
)


# =========================================================
# CONEXIONES
# =========================================================

try:
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )

except KeyError as error:
    st.error(
        "Falta configurar una credencial de Supabase en "
        f"Streamlit Secrets: {error}"
    )
    st.stop()

except Exception as error:
    st.error(
        "No fue posible conectar con Supabase. "
        f"Detalle: {error}"
    )
    st.stop()


try:
    cliente_ia = OpenAI(
        api_key=st.secrets["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": (
                "https://asistente-ia-mantenimiento-automotriz."
                "streamlit.app"
            ),
            "X-OpenRouter-Title": "Taller Postventa IA",
        },
    )

except KeyError:
    cliente_ia = None

except Exception:
    cliente_ia = None


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def normalizar_texto(texto: str) -> str:
    """
    Convierte el texto a minúsculas y elimina tildes.
    """
    texto = texto.lower().strip()

    texto = unicodedata.normalize(
        "NFD",
        texto,
    )

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    return texto


def obtener_nombre_persona(registro: dict | None) -> str:
    """
    Construye el nombre completo de clientes o técnicos.
    """
    if not registro:
        return "Sin nombre"

    nombres = (
        registro.get("nombres")
        or registro.get("nombre")
        or ""
    )

    apellidos = (
        registro.get("apellidos")
        or registro.get("apellido")
        or ""
    )

    nombre_completo = f"{nombres} {apellidos}".strip()

    return nombre_completo or "Sin nombre"


def consultar_tabla(
    nombre_tabla: str,
    limite: int = 500,
) -> list:
    """
    Consulta directamente una tabla de Supabase.
    Si la tabla no existe o ocurre un error, devuelve [].
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


def coincide_con_nombre(
    pregunta_normalizada: str,
    nombre: str,
) -> bool:
    """
    Comprueba si un nombre completo o uno de sus componentes
    aparece dentro de la pregunta.
    """
    nombre_normalizado = normalizar_texto(nombre)

    if nombre_normalizado in pregunta_normalizada:
        return True

    partes = [
        parte
        for parte in nombre_normalizado.split()
        if len(parte) >= 3
    ]

    return bool(partes) and all(
        parte in pregunta_normalizada
        for parte in partes
    )


# =========================================================
# CARGA DE INFORMACIÓN
# =========================================================

@st.cache_data(ttl=30)
def cargar_datos_taller() -> dict:
    """
    Obtiene los datos principales del taller.
    """
    try:
        tecnicos = obtener_tecnicos()
    except Exception:
        tecnicos = []

    try:
        ordenes = obtener_ordenes_trabajo()
    except Exception:
        ordenes = []

    try:
        vehiculos = obtener_vehiculos()
    except Exception:
        vehiculos = []

    clientes = consultar_tabla("clientes")
    citas = consultar_tabla("citas")
    servicios = consultar_tabla("servicios_orden")
    repuestos = consultar_tabla("repuestos_orden")

    return {
        "clientes": clientes,
        "vehiculos": vehiculos,
        "tecnicos": tecnicos,
        "ordenes": ordenes,
        "citas": citas,
        "servicios": servicios,
        "repuestos": repuestos,
    }


# =========================================================
# CONSULTAS DE CANTIDADES
# =========================================================

def responder_cantidades(
    datos: dict,
    pregunta: str,
):
    texto = normalizar_texto(pregunta)

    expresiones_cantidad = [
        "cuantos",
        "cuantas",
        "cantidad",
        "numero de",
        "total de",
    ]

    if not any(
        expresion in texto
        for expresion in expresiones_cantidad
    ):
        return None

    opciones = [
        (
            ["cliente", "clientes"],
            "clientes",
            "clientes",
        ),
        (
            ["vehiculo", "vehiculos"],
            "vehiculos",
            "vehículos",
        ),
        (
            ["tecnico", "tecnicos"],
            "tecnicos",
            "técnicos",
        ),
        (
            ["orden", "ordenes"],
            "ordenes",
            "órdenes de trabajo",
        ),
        (
            ["cita", "citas"],
            "citas",
            "citas",
        ),
        (
            ["servicio", "servicios"],
            "servicios",
            "servicios por orden",
        ),
        (
            ["repuesto", "repuestos"],
            "repuestos",
            "repuestos por orden",
        ),
    ]

    for palabras, clave, etiqueta in opciones:
        if any(palabra in texto for palabra in palabras):
            cantidad = len(datos.get(clave, []))

            return (
                f"Actualmente existen **{cantidad} "
                f"{etiqueta}** registrados en la base "
                f"de datos del taller."
            )

    return None


# =========================================================
# CONSULTAS DE TÉCNICOS
# =========================================================

def responder_tecnicos(
    datos: dict,
    pregunta: str,
):
    texto = normalizar_texto(pregunta)

    if "tecnico" not in texto:
        return None

    tecnicos = datos["tecnicos"]
    ordenes = datos["ordenes"]

    if not tecnicos:
        return (
            "No se encontraron técnicos registrados en "
            "la base de datos."
        )

    # -----------------------------------------------------
    # Técnico con más órdenes asignadas
    # -----------------------------------------------------

    expresiones_mayor_carga = [
        "mas orden",
        "mayor carga",
        "mas trabajo",
        "mas ordenes asignadas",
        "mayor numero de orden",
    ]

    if any(
        expresion in texto
        for expresion in expresiones_mayor_carga
    ):
        conteo = Counter()

        for orden in ordenes:
            tecnico_id = orden.get("tecnico_id")

            if tecnico_id is not None:
                conteo[str(tecnico_id)] += 1

        if not conteo:
            return (
                "Actualmente no existen órdenes de trabajo "
                "asignadas a técnicos."
            )

        mayor_cantidad = max(conteo.values())

        ids_mayor_carga = [
            tecnico_id
            for tecnico_id, cantidad in conteo.items()
            if cantidad == mayor_cantidad
        ]

        resultados = []

        for tecnico_id in ids_mayor_carga:
            tecnico = next(
                (
                    item
                    for item in tecnicos
                    if str(item.get("id")) == tecnico_id
                ),
                None,
            )

            if tecnico:
                nombre = obtener_nombre_persona(tecnico)

                especialidad = (
                    tecnico.get("especialidad")
                    or "No registrada"
                )

                cargo = (
                    tecnico.get("cargo")
                    or "No registrado"
                )

                ordenes_tecnico = [
                    orden
                    for orden in ordenes
                    if str(orden.get("tecnico_id"))
                    == tecnico_id
                ]

                estados = Counter(
                    orden.get("estado") or "Sin estado"
                    for orden in ordenes_tecnico
                )

                detalle_estados = "\n".join(
                    f"  - {estado}: **{cantidad}**"
                    for estado, cantidad in estados.items()
                )

                resultados.append(
                    f"### {nombre}\n"
                    f"- **Órdenes asignadas:** {mayor_cantidad}\n"
                    f"- **Cargo:** {cargo}\n"
                    f"- **Especialidad:** {especialidad}\n"
                    f"- **Distribución por estado:**\n"
                    f"{detalle_estados}"
                )

            else:
                resultados.append(
                    f"El técnico con ID **{tecnico_id}** "
                    f"tiene **{mayor_cantidad} órdenes**, "
                    f"pero no se encontró su registro."
                )

        if len(resultados) == 1:
            return (
                "El técnico con más órdenes de trabajo "
                "asignadas es:\n\n"
                + resultados[0]
            )

        return (
            "Existe un empate entre los técnicos con mayor "
            "cantidad de órdenes asignadas:\n\n"
            + "\n\n".join(resultados)
        )

    # -----------------------------------------------------
    # Lista de técnicos y carga de trabajo
    # -----------------------------------------------------

    expresiones_lista = [
        "que tecnicos",
        "cuales tecnicos",
        "lista de tecnicos",
        "tecnicos trabajan",
        "mostrar tecnicos",
        "todos los tecnicos",
        "cada tecnico",
    ]

    if any(
        expresion in texto
        for expresion in expresiones_lista
    ):
        lineas = []

        for tecnico in tecnicos:
            tecnico_id = tecnico.get("id")
            nombre = obtener_nombre_persona(tecnico)

            especialidad = (
                tecnico.get("especialidad")
                or "No registrada"
            )

            cargo = (
                tecnico.get("cargo")
                or "No registrado"
            )

            activo = tecnico.get("activo", True)

            estado = (
                "Activo"
                if activo
                else "Inactivo"
            )

            total_ordenes = sum(
                1
                for orden in ordenes
                if str(orden.get("tecnico_id"))
                == str(tecnico_id)
            )

            ordenes_activas = sum(
                1
                for orden in ordenes
                if (
                    str(orden.get("tecnico_id"))
                    == str(tecnico_id)
                    and orden.get("estado")
                    not in [
                        "Finalizada",
                        "Entregada",
                        "Cancelada",
                    ]
                )
            )

            lineas.append(
                f"- **{nombre}** — {cargo}; "
                f"especialidad: {especialidad}; "
                f"estado: {estado}; "
                f"órdenes totales: {total_ordenes}; "
                f"órdenes activas: {ordenes_activas}."
            )

        return (
            f"Se encontraron **{len(tecnicos)} técnicos** "
            f"registrados:\n\n"
            + "\n".join(lineas)
        )

    # -----------------------------------------------------
    # Técnico con menor carga de trabajo
    # -----------------------------------------------------

    if (
        "menos orden" in texto
        or "menor carga" in texto
        or "mas disponible" in texto
        or "tecnico disponible" in texto
    ):
        cargas = []

        for tecnico in tecnicos:
            if not tecnico.get("activo", True):
                continue

            tecnico_id = tecnico.get("id")

            ordenes_activas = sum(
                1
                for orden in ordenes
                if (
                    str(orden.get("tecnico_id"))
                    == str(tecnico_id)
                    and orden.get("estado")
                    not in [
                        "Finalizada",
                        "Entregada",
                        "Cancelada",
                    ]
                )
            )

            cargas.append(
                (
                    ordenes_activas,
                    tecnico,
                )
            )

        if not cargas:
            return (
                "No existen técnicos activos disponibles "
                "para analizar."
            )

        menor_carga = min(
            cantidad
            for cantidad, _ in cargas
        )

        tecnicos_disponibles = [
            tecnico
            for cantidad, tecnico in cargas
            if cantidad == menor_carga
        ]

        lineas = []

        for tecnico in tecnicos_disponibles:
            nombre = obtener_nombre_persona(tecnico)

            especialidad = (
                tecnico.get("especialidad")
                or "No registrada"
            )

            lineas.append(
                f"- **{nombre}** — {especialidad}; "
                f"órdenes activas: **{menor_carga}**."
            )

        return (
            "El técnico o los técnicos con menor carga "
            "de trabajo son:\n\n"
            + "\n".join(lineas)
        )

    # -----------------------------------------------------
    # Buscar técnico por nombre
    # -----------------------------------------------------

    for tecnico in tecnicos:
        nombre = obtener_nombre_persona(tecnico)

        if coincide_con_nombre(texto, nombre):
            tecnico_id = tecnico.get("id")

            especialidad = (
                tecnico.get("especialidad")
                or "No registrada"
            )

            cargo = (
                tecnico.get("cargo")
                or "No registrado"
            )

            activo = tecnico.get("activo", True)

            total_ordenes = sum(
                1
                for orden in ordenes
                if str(orden.get("tecnico_id"))
                == str(tecnico_id)
            )

            ordenes_activas = [
                orden
                for orden in ordenes
                if (
                    str(orden.get("tecnico_id"))
                    == str(tecnico_id)
                    and orden.get("estado")
                    not in [
                        "Finalizada",
                        "Entregada",
                        "Cancelada",
                    ]
                )
            ]

            detalle_ordenes = ""

            if ordenes_activas:
                lineas = []

                for orden in ordenes_activas[:10]:
                    codigo = orden.get("id")
                    estado = (
                        orden.get("estado")
                        or "Sin estado"
                    )

                    vehiculo = (
                        orden.get("vehiculos")
                        or {}
                    )

                    placa = (
                        vehiculo.get("placa")
                        or "Sin placa"
                    )

                    lineas.append(
                        f"- OT-{int(codigo):05d} — "
                        f"{placa} — {estado}"
                        if isinstance(codigo, int)
                        else (
                            f"- Orden {codigo} — "
                            f"{placa} — {estado}"
                        )
                    )

                detalle_ordenes = (
                    "\n\n**Órdenes activas:**\n"
                    + "\n".join(lineas)
                )

            return (
                f"### Información de {nombre}\n\n"
                f"- **Cargo:** {cargo}\n"
                f"- **Especialidad:** {especialidad}\n"
                f"- **Estado:** "
                f"{'Activo' if activo else 'Inactivo'}\n"
                f"- **Total de órdenes asignadas:** "
                f"{total_ordenes}\n"
                f"- **Órdenes activas:** "
                f"{len(ordenes_activas)}"
                f"{detalle_ordenes}"
            )

    return None


# =========================================================
# CONSULTAS DE ÓRDENES
# =========================================================

def responder_ordenes(
    datos: dict,
    pregunta: str,
):
    texto = normalizar_texto(pregunta)

    if "orden" not in texto:
        return None

    ordenes = datos["ordenes"]

    if not ordenes:
        return (
            "No existen órdenes de trabajo registradas "
            "en la base de datos."
        )

    estados_validos = {
        "pendiente": "Pendiente",
        "diagnostico": "Diagnóstico",
        "en proceso": "En proceso",
        "proceso": "En proceso",
        "espera de repuestos": "En espera de repuestos",
        "finalizada": "Finalizada",
        "finalizadas": "Finalizada",
        "entregada": "Entregada",
        "entregadas": "Entregada",
        "cancelada": "Cancelada",
        "canceladas": "Cancelada",
    }

    for expresion, estado_real in estados_validos.items():
        if expresion in texto:
            encontradas = [
                orden
                for orden in ordenes
                if orden.get("estado") == estado_real
            ]

            return (
                f"Actualmente existen **{len(encontradas)} "
                f"órdenes** con estado **{estado_real}**."
            )

    if (
        "sin tecnico" in texto
        or "no asignada" in texto
        or "no asignadas" in texto
    ):
        sin_tecnico = [
            orden
            for orden in ordenes
            if orden.get("tecnico_id") is None
        ]

        return (
            f"Actualmente existen **{len(sin_tecnico)} "
            f"órdenes sin técnico asignado**."
        )

    patron_orden = re.search(
        r"(?:ot[-\s]?|orden(?:\s+numero)?\s*)"
        r"(\d+)",
        texto,
    )

    if patron_orden:
        orden_id = int(patron_orden.group(1))

        orden = next(
            (
                item
                for item in ordenes
                if item.get("id") == orden_id
            ),
            None,
        )

        if not orden:
            return (
                f"No se encontró la orden de trabajo "
                f"**OT-{orden_id:05d}**."
            )

        vehiculo = orden.get("vehiculos") or {}
        tecnico = orden.get("tecnicos") or {}

        placa = (
            vehiculo.get("placa")
            or "Sin placa"
        )

        descripcion_vehiculo = " ".join(
            (
                f'{vehiculo.get("marca", "")} '
                f'{vehiculo.get("modelo", "")} '
                f'{vehiculo.get("anio", "")}'
            ).split()
        )

        nombre_tecnico = obtener_nombre_persona(
            tecnico
        )

        return (
            f"### Orden OT-{orden_id:05d}\n\n"
            f"- **Vehículo:** {placa} — "
            f"{descripcion_vehiculo}\n"
            f"- **Técnico:** {nombre_tecnico}\n"
            f"- **Estado:** "
            f"{orden.get('estado') or 'Sin estado'}\n"
            f"- **Motivo de ingreso:** "
            f"{orden.get('motivo_ingreso') or 'No registrado'}\n"
            f"- **Diagnóstico:** "
            f"{orden.get('diagnostico') or 'No registrado'}\n"
            f"- **Fecha de ingreso:** "
            f"{orden.get('fecha_ingreso') or 'No registrada'}\n"
            f"- **Costo estimado:** "
            f"${float(orden.get('costo_estimado') or 0):,.2f}\n"
            f"- **Costo final:** "
            f"${float(orden.get('costo_final') or 0):,.2f}"
        )

    return None


# =========================================================
# CONSULTAS DE CITAS
# =========================================================

def responder_citas(
    datos: dict,
    pregunta: str,
):
    texto = normalizar_texto(pregunta)

    if "cita" not in texto:
        return None

    citas = datos["citas"]

    if not citas:
        return (
            "No existen citas registradas en la base "
            "de datos."
        )

    if "manana" in texto:
        fecha_buscada = date.today() + timedelta(days=1)

    elif "hoy" in texto:
        fecha_buscada = date.today()

    else:
        fecha_buscada = None

    if fecha_buscada is None:
        return (
            f"Actualmente existen **{len(citas)} citas** "
            f"registradas en el sistema."
        )

    citas_encontradas = []

    for cita in citas:
        fecha = (
            cita.get("fecha_cita")
            or cita.get("fecha")
            or cita.get("fecha_hora")
            or ""
        )

        if str(fecha).startswith(
            fecha_buscada.isoformat()
        ):
            citas_encontradas.append(cita)

    if not citas_encontradas:
        return (
            f"No existen citas registradas para el "
            f"**{fecha_buscada.strftime('%d/%m/%Y')}**."
        )

    lineas = []

    for cita in citas_encontradas:
        fecha = (
            cita.get("fecha_cita")
            or cita.get("fecha")
            or "No registrada"
        )

        hora = (
            cita.get("hora_cita")
            or cita.get("hora")
            or cita.get("fecha_hora")
            or "No registrada"
        )

        motivo = (
            cita.get("motivo")
            or cita.get("descripcion")
            or cita.get("servicio")
            or "No registrado"
        )

        estado = (
            cita.get("estado")
            or "No registrado"
        )

        lineas.append(
            f"- **{fecha} {hora}** — "
            f"{motivo} — Estado: {estado}."
        )

    return (
        f"Se encontraron **{len(citas_encontradas)} "
        f"citas** para el "
        f"**{fecha_buscada.strftime('%d/%m/%Y')}**:\n\n"
        + "\n".join(lineas)
    )


# =========================================================
# CONSULTAS DE VEHÍCULOS
# =========================================================

def responder_vehiculos(
    datos: dict,
    pregunta: str,
):
    texto = normalizar_texto(pregunta)

    if (
        "vehiculo" not in texto
        and "placa" not in texto
    ):
        return None

    vehiculos = datos["vehiculos"]

    patron_placa = re.search(
        r"\b[A-Z]{2,3}[-\s]?\d{3,4}\b",
        pregunta.upper(),
    )

    if not patron_placa:
        return None

    placa_buscada = (
        patron_placa.group(0)
        .replace("-", "")
        .replace(" ", "")
        .upper()
    )

    for vehiculo in vehiculos:
        placa = str(
            vehiculo.get("placa")
            or ""
        )

        placa_normalizada = (
            placa
            .replace("-", "")
            .replace(" ", "")
            .upper()
        )

        if placa_normalizada == placa_buscada:
            cliente = (
                vehiculo.get("clientes")
                or {}
            )

            nombre_cliente = obtener_nombre_persona(
                cliente
            )

            return (
                f"### Vehículo {placa}\n\n"
                f"- **Marca:** "
                f"{vehiculo.get('marca') or 'No registrada'}\n"
                f"- **Modelo:** "
                f"{vehiculo.get('modelo') or 'No registrado'}\n"
                f"- **Año:** "
                f"{vehiculo.get('anio') or 'No registrado'}\n"
                f"- **Kilometraje:** "
                f"{vehiculo.get('kilometraje') or 0} km\n"
                f"- **Cliente:** {nombre_cliente}\n"
                f"- **Estado:** "
                f"{'Activo' if vehiculo.get('activo', True) else 'Inactivo'}"
            )

    return (
        f"No se encontró un vehículo con la placa "
        f"**{patron_placa.group(0)}**."
    )


# =========================================================
# DETECTOR DE CONSULTAS DE LA BASE DE DATOS
# =========================================================

def consultar_base_de_datos(
    pregunta: str,
):
    datos = cargar_datos_taller()

    funciones = [
        responder_cantidades,
        responder_tecnicos,
        responder_ordenes,
        responder_citas,
        responder_vehiculos,
    ]

    for funcion in funciones:
        respuesta = funcion(
            datos,
            pregunta,
        )

        if respuesta:
            return respuesta

    return None


# =========================================================
# ASISTENTE TÉCNICO DE OPENROUTER
# =========================================================

INSTRUCCIONES_IA = """
Eres el asistente técnico virtual del taller automotriz
Doctor Fierros.

Responde siempre en español, con lenguaje profesional,
claro y comprensible.

Puedes ayudar con:

- mantenimiento preventivo;
- mantenimiento correctivo;
- diagnóstico inicial;
- códigos OBD-II;
- frenos;
- suspensión;
- dirección;
- motor;
- transmisión;
- electricidad automotriz;
- atención posventa;
- redacción de observaciones técnicas.

Cuando se describa una falla, responde con:

1. Resumen del problema.
2. Posibles causas.
3. Pruebas recomendadas.
4. Herramientas necesarias.
5. Nivel de urgencia.
6. Recomendación final.

No confirmes que una pieza está dañada sin inspección,
mediciones o pruebas técnicas.

Si existe riesgo para la seguridad, indica claramente
que el vehículo no debería circular.

No inventes clientes, técnicos, vehículos, citas ni
órdenes de trabajo.
"""


def consultar_ia_tecnica(
    pregunta: str,
    historial: list,
) -> str:
    if cliente_ia is None:
        return (
            "La consulta no coincide con una función de la "
            "base de datos y la clave OPENROUTER_API_KEY no "
            "está configurada correctamente."
        )

    mensajes = [
        {
            "role": "system",
            "content": INSTRUCCIONES_IA,
        }
    ]

    mensajes.extend(
        historial[-10:]
    )

    mensajes.append(
        {
            "role": "user",
            "content": pregunta,
        }
    )

    try:
        respuesta = (
            cliente_ia
            .chat
            .completions
            .create(
                model="openrouter/free",
                messages=mensajes,
                temperature=0.3,
                max_tokens=800,
            )
        )

        texto = (
            respuesta
            .choices[0]
            .message
            .content
        )

        return (
            texto
            or "El modelo no produjo una respuesta."
        )

    except Exception as error:
        detalle = str(error)

        if "401" in detalle:
            return (
                "La clave de OpenRouter no es válida o "
                "no está configurada correctamente."
            )

        if "429" in detalle:
            return (
                "El servicio gratuito alcanzó temporalmente "
                "su límite. Espera unos minutos e intenta "
                "nuevamente."
            )

        return (
            "No fue posible consultar el asistente IA.\n\n"
            f"Detalle técnico: {detalle}"
        )


# =========================================================
# HISTORIAL DEL CHAT
# =========================================================

if "historial_ia" not in st.session_state:
    st.session_state.historial_ia = [
        {
            "role": "assistant",
            "content": (
                "Hola. Soy el asistente inteligente del taller "
                "Doctor Fierros. Puedo consultar información de "
                "Supabase y responder preguntas técnicas."
            ),
        }
    ]


# =========================================================
# BOTONES
# =========================================================

columna_1, columna_2 = st.columns(
    [5, 1]
)

with columna_2:
    if st.button(
        "🗑️ Limpiar chat",
        use_container_width=True,
    ):
        st.session_state.historial_ia = [
            {
                "role": "assistant",
                "content": (
                    "La conversación fue reiniciada. "
                    "Escribe una nueva consulta."
                ),
            }
        ]

        st.rerun()


if st.button(
    "🔄 Actualizar datos de Supabase",
):
    st.cache_data.clear()
    st.success(
        "Los datos fueron actualizados."
    )
    st.rerun()


# =========================================================
# PREGUNTAS SUGERIDAS
# =========================================================

with st.expander(
    "💡 Preguntas para probar"
):
    st.markdown(
        """
        **Consultas de la base de datos**

        - ¿Cuántos clientes hay registrados?
        - ¿Cuántos técnicos trabajan en el taller?
        - ¿Quién es el técnico con más órdenes asignadas?
        - ¿Qué técnico tiene menor carga de trabajo?
        - ¿Qué técnicos trabajan en el taller?
        - ¿Cuántas órdenes están pendientes?
        - ¿Cuántas órdenes están en proceso?
        - ¿Cuántas órdenes están sin técnico?
        - Muéstrame la orden OT-00001.
        - ¿Qué citas existen para mañana?
        - ¿Qué información existe del vehículo ABC-1234?

        **Consultas técnicas**

        - ¿Qué significa el código P0300?
        - ¿Qué se debe revisar si un vehículo vibra al frenar?
        - ¿Qué mantenimiento corresponde a los 80 000 km?
        - Redacta una recomendación por desgaste de pastillas.
        """
    )


# =========================================================
# MOSTRAR HISTORIAL
# =========================================================

for mensaje in st.session_state.historial_ia:
    with st.chat_message(
        mensaje["role"]
    ):
        st.markdown(
            mensaje["content"]
        )


# =========================================================
# ENTRADA DEL USUARIO
# =========================================================

pregunta = st.chat_input(
    "Escribe una consulta sobre el taller "
    "o sobre mecánica automotriz..."
)


if pregunta:
    historial_anterior = (
        st.session_state
        .historial_ia
        .copy()
    )

    st.session_state.historial_ia.append(
        {
            "role": "user",
            "content": pregunta,
        }
    )

    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant"):
        with st.spinner(
            "Consultando información..."
        ):
            respuesta_bd = (
                consultar_base_de_datos(
                    pregunta
                )
            )

            if respuesta_bd:
                respuesta_final = respuesta_bd

            else:
                respuesta_final = (
                    consultar_ia_tecnica(
                        pregunta,
                        historial_anterior,
                    )
                )

        st.markdown(
            respuesta_final
        )

    st.session_state.historial_ia.append(
        {
            "role": "assistant",
            "content": respuesta_final,
        }
    )