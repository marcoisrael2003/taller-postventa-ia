from collections import Counter
from datetime import date, timedelta
import re
import unicodedata

import streamlit as st
from openai import OpenAI

from services.supabase_service import (
    obtener_citas_completas,
    obtener_clientes,
    obtener_ordenes_trabajo,
    obtener_repuestos_orden,
    obtener_servicios_orden,
    obtener_tecnicos,
    obtener_vehiculos,
)

st.set_page_config(page_title="Asistente IA", page_icon="🤖", layout="wide")
st.title("🤖 Asistente Inteligente del Taller")
st.caption("Consulta datos reales de Supabase y realiza preguntas técnicas automotrices.")


def normalizar(texto):
    texto = unicodedata.normalize("NFD", str(texto).lower().strip())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def contiene(texto, opciones):
    return any(opcion in texto for opcion in opciones)


def nombre_persona(registro):
    registro = registro or {}
    nombre = f"{registro.get('nombres', '')} {registro.get('apellidos', '')}".strip()
    return nombre or "Sin nombre registrado"


def placa_normalizada(placa):
    return re.sub(r"[^A-Z0-9]", "", str(placa or "").upper())


def numero(valor, defecto=0):
    try:
        return float(valor or defecto)
    except (TypeError, ValueError):
        return float(defecto)


@st.cache_data(ttl=30)
def cargar_datos():
    datos = {}
    funciones = {
        "clientes": obtener_clientes,
        "vehiculos": obtener_vehiculos,
        "tecnicos": obtener_tecnicos,
        "ordenes": obtener_ordenes_trabajo,
        "citas": obtener_citas_completas,
        "servicios": obtener_servicios_orden,
        "repuestos": obtener_repuestos_orden,
    }

    errores = []
    for clave, funcion in funciones.items():
        try:
            datos[clave] = funcion()
        except Exception as error:
            datos[clave] = []
            errores.append(f"{clave}: {error}")

    datos["errores"] = errores
    return datos


def responder_cantidades(datos, pregunta):
    texto = normalizar(pregunta)

    if not contiene(
        texto,
        ["cuanto", "cuantos", "cuanta", "cuantas", "cantidad", "total", "tenemos", "existen", "hay"],
    ):
        return None

    if contiene(texto, ["vehiculo", "carro", "auto"]):
        vehiculos = datos["vehiculos"]
        activos = [v for v in vehiculos if v.get("activo", True)]
        return (
            f"Actualmente existen **{len(vehiculos)} vehículos registrados**.\n\n"
            f"- Activos: **{len(activos)}**\n"
            f"- Inactivos: **{len(vehiculos) - len(activos)}**"
        )

    if "cliente" in texto:
        return f"Actualmente existen **{len(datos['clientes'])} clientes registrados**."

    if "tecnico" in texto:
        return f"Actualmente existen **{len(datos['tecnicos'])} técnicos registrados**."

    if "orden" in texto:
        return f"Actualmente existen **{len(datos['ordenes'])} órdenes registradas**."

    if "cita" in texto:
        return f"Actualmente existen **{len(datos['citas'])} citas registradas**."

    if "servicio" in texto:
        return f"Actualmente existen **{len(datos['servicios'])} servicios registrados**."

    if "repuesto" in texto:
        return f"Actualmente existen **{len(datos['repuestos'])} repuestos registrados**."

    return None


def responder_vehiculos(datos, pregunta):
    texto = normalizar(pregunta)
    vehiculos = datos["vehiculos"]

    marcas = sorted({
        normalizar(v.get("marca", ""))
        for v in vehiculos
        if v.get("marca")
    })
    modelos = sorted({
        normalizar(v.get("modelo", ""))
        for v in vehiculos
        if v.get("modelo")
    })
    colores = sorted({
        normalizar(v.get("color", ""))
        for v in vehiculos
        if v.get("color")
    })

    relacionado = (
        contiene(
            texto,
            [
                "vehiculo", "carro", "auto", "placa", "marca", "modelo",
                "kilometraje", "color", "anio", "antiguo", "nuevo",
            ],
        )
        or any(marca in texto for marca in marcas)
        or any(modelo in texto for modelo in modelos)
        or any(color in texto for color in colores)
    )

    if not relacionado:
        return None

    if not vehiculos:
        return "No existen vehículos registrados."

    patron_placa = re.search(r"\b[A-Z]{3,4}[-\s]?\d{3,4}\b", pregunta.upper())
    if patron_placa:
        buscada = placa_normalizada(patron_placa.group(0))
        vehiculo = next(
            (v for v in vehiculos if placa_normalizada(v.get("placa")) == buscada),
            None,
        )

        if not vehiculo:
            return f"No se encontró un vehículo con la placa **{patron_placa.group(0)}**."

        cliente = vehiculo.get("clientes") or {}
        return (
            f"### Vehículo {vehiculo.get('placa')}\n\n"
            f"- **Marca:** {vehiculo.get('marca') or 'No registrada'}\n"
            f"- **Modelo:** {vehiculo.get('modelo') or 'No registrado'}\n"
            f"- **Año:** {vehiculo.get('anio') or 'No registrado'}\n"
            f"- **Color:** {vehiculo.get('color') or 'No registrado'}\n"
            f"- **Kilometraje:** {int(numero(vehiculo.get('kilometraje')))} km\n"
            f"- **VIN:** {vehiculo.get('vin') or 'No registrado'}\n"
            f"- **Propietario:** {nombre_persona(cliente)}\n"
            f"- **Cédula:** {cliente.get('cedula') or 'No registrada'}\n"
            f"- **Estado:** {'Activo' if vehiculo.get('activo', True) else 'Inactivo'}"
        )

    marca = next(
        (m for m in marcas if re.search(rf"\b{re.escape(m)}\b", texto)),
        None,
    )
    if marca:
        encontrados = [
            v for v in vehiculos
            if normalizar(v.get("marca", "")) == marca
        ]
        nombre_marca = encontrados[0].get("marca") if encontrados else marca.title()

        if contiene(texto, ["cuanto", "cuantos", "cantidad", "total", "hay", "tenemos"]):
            return (
                f"Hay **{len(encontrados)} vehículo(s) de la marca "
                f"{nombre_marca}** registrados."
            )

        lineas = [
            f"- **{v.get('placa')}** — {v.get('marca')} {v.get('modelo')} "
            f"{v.get('anio')}; propietario: {nombre_persona(v.get('clientes'))}."
            for v in encontrados
        ]
        return f"Vehículos {nombre_marca}:\n\n" + "\n".join(lineas)

    modelo = next(
        (m for m in modelos if re.search(rf"\b{re.escape(m)}\b", texto)),
        None,
    )
    if modelo:
        encontrados = [
            v for v in vehiculos
            if normalizar(v.get("modelo", "")) == modelo
        ]
        if contiene(texto, ["cuanto", "cuantos", "cantidad", "hay", "tenemos"]):
            return f"Hay **{len(encontrados)} vehículo(s) del modelo {modelo.title()}**."

        lineas = [
            f"- **{v.get('placa')}** — {v.get('marca')} {v.get('modelo')} {v.get('anio')}."
            for v in encontrados
        ]
        return "Vehículos encontrados:\n\n" + "\n".join(lineas)

    if contiene(texto, ["por marca", "cada marca", "cantidad por marca"]):
        conteo = Counter(v.get("marca") or "Sin marca" for v in vehiculos)
        return "### Vehículos por marca\n\n" + "\n".join(
            f"- **{marca}:** {cantidad}"
            for marca, cantidad in conteo.most_common()
        )

    if contiene(texto, ["marca mas frecuente", "marca mas registrada", "marca predominante"]):
        marca_frecuente, cantidad = Counter(
            v.get("marca") or "Sin marca" for v in vehiculos
        ).most_common(1)[0]
        return (
            f"La marca más frecuente es **{marca_frecuente}**, "
            f"con **{cantidad} vehículo(s)**."
        )

    patron_anio = re.search(r"\b(19|20)\d{2}\b", texto)
    if patron_anio:
        anio = int(patron_anio.group(0))
        encontrados = [v for v in vehiculos if int(v.get("anio") or 0) == anio]

        if contiene(texto, ["cuanto", "cuantos", "cantidad", "hay", "tenemos"]):
            return f"Hay **{len(encontrados)} vehículo(s) del año {anio}**."

        if not encontrados:
            return f"No existen vehículos del año **{anio}**."

        return f"Vehículos del año **{anio}**:\n\n" + "\n".join(
            f"- **{v.get('placa')}** — {v.get('marca')} {v.get('modelo')}."
            for v in encontrados
        )

    color = next(
        (c for c in colores if re.search(rf"\b{re.escape(c)}\b", texto)),
        None,
    )
    if color:
        encontrados = [
            v for v in vehiculos
            if normalizar(v.get("color", "")) == color
        ]

        if contiene(texto, ["cuanto", "cuantos", "cantidad", "hay", "tenemos"]):
            return f"Hay **{len(encontrados)} vehículo(s) de color {color.title()}**."

        return f"Vehículos de color **{color.title()}**:\n\n" + "\n".join(
            f"- **{v.get('placa')}** — {v.get('marca')} {v.get('modelo')} {v.get('anio')}."
            for v in encontrados
        )

    if contiene(texto, ["mayor kilometraje", "mas kilometraje", "mas recorrido"]):
        vehiculo = max(vehiculos, key=lambda v: numero(v.get("kilometraje")))
        return (
            f"El vehículo con mayor kilometraje es **{vehiculo.get('placa')}**, "
            f"{vehiculo.get('marca')} {vehiculo.get('modelo')} "
            f"{vehiculo.get('anio')}, con "
            f"**{int(numero(vehiculo.get('kilometraje')))} km**."
        )

    if contiene(texto, ["menor kilometraje", "menos kilometraje", "menos recorrido"]):
        vehiculo = min(vehiculos, key=lambda v: numero(v.get("kilometraje")))
        return (
            f"El vehículo con menor kilometraje es **{vehiculo.get('placa')}**, "
            f"{vehiculo.get('marca')} {vehiculo.get('modelo')} "
            f"{vehiculo.get('anio')}, con "
            f"**{int(numero(vehiculo.get('kilometraje')))} km**."
        )

    if contiene(texto, ["mas antiguo", "vehiculo antiguo"]):
        vehiculo = min(vehiculos, key=lambda v: int(v.get("anio") or 9999))
        return (
            f"El vehículo más antiguo es **{vehiculo.get('placa')}**, "
            f"{vehiculo.get('marca')} {vehiculo.get('modelo')}, "
            f"año **{vehiculo.get('anio')}**."
        )

    if contiene(texto, ["mas nuevo", "vehiculo nuevo", "mas reciente"]):
        vehiculo = max(vehiculos, key=lambda v: int(v.get("anio") or 0))
        return (
            f"El vehículo más nuevo es **{vehiculo.get('placa')}**, "
            f"{vehiculo.get('marca')} {vehiculo.get('modelo')}, "
            f"año **{vehiculo.get('anio')}**."
        )

    if contiene(
        texto,
        [
            "que vehiculos", "cuales vehiculos", "lista de vehiculos",
            "mostrar vehiculos", "vehiculos registrados", "todos los vehiculos",
        ],
    ):
        lineas = [
            f"- **{v.get('placa')}** — {v.get('marca')} {v.get('modelo')} "
            f"{v.get('anio')}; propietario: {nombre_persona(v.get('clientes'))}; "
            f"kilometraje: {int(numero(v.get('kilometraje')))} km."
            for v in vehiculos
        ]
        return f"Se encontraron **{len(vehiculos)} vehículos**:\n\n" + "\n".join(lineas)

    return None


def responder_tecnicos(datos, pregunta):
    texto = normalizar(pregunta)
    if "tecnico" not in texto:
        return None

    tecnicos = datos["tecnicos"]
    ordenes = datos["ordenes"]

    if contiene(texto, ["mas orden", "mayor carga", "mas trabajo"]):
        conteo = Counter(
            str(o.get("tecnico_id"))
            for o in ordenes
            if o.get("tecnico_id") is not None
        )

        if not conteo:
            return "No existen órdenes asignadas a técnicos."

        mayor = max(conteo.values())
        ids = [i for i, cantidad in conteo.items() if cantidad == mayor]
        lineas = []

        for tecnico_id in ids:
            tecnico = next(
                (t for t in tecnicos if str(t.get("id")) == tecnico_id),
                None,
            )
            if tecnico:
                lineas.append(
                    f"- **{nombre_persona(tecnico)}** — {mayor} órdenes."
                )

        return "Técnico(s) con más órdenes:\n\n" + "\n".join(lineas)

    if contiene(texto, ["lista de tecnicos", "que tecnicos", "todos los tecnicos"]):
        return f"Se encontraron **{len(tecnicos)} técnicos**:\n\n" + "\n".join(
            f"- **{nombre_persona(t)}** — "
            f"{t.get('especialidad') or 'Sin especialidad'}."
            for t in tecnicos
        )

    return None


def responder_ordenes(datos, pregunta):
    texto = normalizar(pregunta)
    if "orden" not in texto:
        return None

    ordenes = datos["ordenes"]
    estados = [
        "pendiente",
        "diagnostico",
        "en proceso",
        "finalizada",
        "entregada",
        "cancelada",
    ]

    for estado in estados:
        if estado in texto:
            cantidad = sum(
                1
                for orden in ordenes
                if normalizar(orden.get("estado", "")) == estado
            )
            return f"Existen **{cantidad} órdenes** con estado **{estado.title()}**."

    if contiene(texto, ["sin tecnico", "sin asignar"]):
        cantidad = sum(1 for orden in ordenes if orden.get("tecnico_id") is None)
        return f"Existen **{cantidad} órdenes sin técnico asignado**."

    return None


def responder_citas(datos, pregunta):
    texto = normalizar(pregunta)
    if "cita" not in texto:
        return None

    citas = datos["citas"]

    if "hoy" in texto:
        fecha = date.today()
    elif "manana" in texto:
        fecha = date.today() + timedelta(days=1)
    else:
        return f"Actualmente existen **{len(citas)} citas registradas**."

    encontradas = [
        cita
        for cita in citas
        if str(cita.get("fecha_cita", "")).startswith(fecha.isoformat())
    ]

    if not encontradas:
        return f"No existen citas para el **{fecha.strftime('%d/%m/%Y')}**."

    return f"Citas para el **{fecha.strftime('%d/%m/%Y')}**:\n\n" + "\n".join(
        f"- **{cita.get('hora_cita') or 'Sin hora'}** — "
        f"{cita.get('placa') or 'Sin placa'} — "
        f"{cita.get('tipo_servicio') or cita.get('motivo') or 'Sin servicio'}."
        for cita in encontradas
    )


def consultar_bd(pregunta):
    datos = cargar_datos()

    for funcion in [
        responder_cantidades,
        responder_vehiculos,
        responder_tecnicos,
        responder_ordenes,
        responder_citas,
    ]:
        respuesta = funcion(datos, pregunta)
        if respuesta:
            return respuesta

    return None


def parece_consulta_sistema(pregunta):
    texto = normalizar(pregunta)
    datos = cargar_datos()

    marcas = [
        normalizar(v.get("marca", ""))
        for v in datos["vehiculos"]
        if v.get("marca")
    ]
    modelos = [
        normalizar(v.get("modelo", ""))
        for v in datos["vehiculos"]
        if v.get("modelo")
    ]

    return (
        contiene(
            texto,
            [
                "taller", "cliente", "vehiculo", "carro", "auto", "tecnico",
                "orden", "cita", "registrado", "tenemos", "placa", "marca",
                "modelo", "kilometraje", "propietario",
            ],
        )
        or any(marca in texto for marca in marcas)
        or any(modelo in texto for modelo in modelos)
    )


try:
    cliente_ia = OpenAI(
        api_key=st.secrets["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )
except Exception:
    cliente_ia = None


def consultar_ia(pregunta, historial):
    if cliente_ia is None:
        return "OPENROUTER_API_KEY no está configurada correctamente."

    mensajes = [
        {
            "role": "system",
            "content": (
                "Eres un asistente técnico automotriz. Responde en español. "
                "No inventes datos del taller ni de Supabase."
            ),
        }
    ]
    mensajes.extend(historial[-8:])
    mensajes.append({"role": "user", "content": pregunta})

    try:
        respuesta = cliente_ia.chat.completions.create(
            model="openrouter/free",
            messages=mensajes,
            temperature=0.3,
            max_tokens=700,
        )
        return respuesta.choices[0].message.content or "Sin respuesta."
    except Exception as error:
        return f"No fue posible consultar OpenRouter: {error}"


if "historial_ia" not in st.session_state:
    st.session_state.historial_ia = [
        {
            "role": "assistant",
            "content": (
                "Hola. Puedo consultar datos reales del taller y responder "
                "preguntas técnicas automotrices."
            ),
        }
    ]

col1, col2 = st.columns([5, 1])

with col2:
    if st.button("🗑️ Limpiar", use_container_width=True):
        st.session_state.historial_ia = []
        st.rerun()

if st.button("🔄 Actualizar datos"):
    st.cache_data.clear()
    st.success("Datos actualizados.")

with st.expander("💡 Preguntas para probar"):
    st.markdown(
        """
- ¿Cuántos Chevrolet hay registrados?
- ¿Qué vehículos son Toyota?
- ¿Cuántos vehículos hay por marca?
- ¿Cuál es la marca más frecuente?
- ¿Cuál es el vehículo con mayor kilometraje?
- ¿Cuál es el vehículo más antiguo?
- ¿Qué vehículos son del año 2020?
- ¿Qué vehículos son de color negro?
- Muéstrame la información del vehículo PBC-2145.
- ¿Quién es el propietario del vehículo PBC-2145?
- ¿Quién es el técnico con más órdenes?
- ¿Cuántas órdenes están pendientes?
- ¿Qué citas hay para mañana?
        """
    )

for mensaje in st.session_state.historial_ia:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

pregunta = st.chat_input("Escribe tu consulta...")

if pregunta:
    historial_anterior = st.session_state.historial_ia.copy()
    st.session_state.historial_ia.append({"role": "user", "content": pregunta})

    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando..."):
            respuesta = consultar_bd(pregunta)

            if not respuesta and parece_consulta_sistema(pregunta):
                respuesta = (
                    "La pregunta parece referirse a datos del taller, pero no "
                    "pude identificarla. Prueba indicando vehículo, marca, placa, "
                    "técnico, orden o cita."
                )

            if not respuesta:
                respuesta = consultar_ia(pregunta, historial_anterior)

        st.markdown(respuesta)

    st.session_state.historial_ia.append(
        {"role": "assistant", "content": respuesta}
    )