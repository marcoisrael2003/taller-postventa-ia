import streamlit as st
from openai import OpenAI


st.set_page_config(
    page_title="Asistente IA",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Asistente IA Automotriz")

st.write(
    "Consulta sobre mantenimiento, fallas automotrices, códigos OBD-II "
    "y recomendaciones para órdenes de trabajo."
)

st.warning(
    "Las respuestas son orientativas y no reemplazan una inspección "
    "física ni un diagnóstico realizado por un técnico."
)


# =========================================================
# CONEXIÓN CON OPENROUTER
# =========================================================

try:
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

except KeyError:
    st.error(
        "No se encontró OPENROUTER_API_KEY en los Secrets de Streamlit."
    )
    st.stop()


# =========================================================
# PERSONALIDAD DEL ASISTENTE
# =========================================================

INSTRUCCIONES = """
Eres el asistente técnico virtual de un taller automotriz de servicio
postventa llamado Doctor Fierros.

Responde siempre en español y con lenguaje profesional, claro y breve.

Puedes ayudar con:

- mantenimiento preventivo;
- mantenimiento correctivo;
- diagnóstico inicial de fallas;
- interpretación de códigos OBD-II;
- sistemas de frenos;
- suspensión y dirección;
- motor;
- transmisión;
- sistema eléctrico;
- redacción de observaciones técnicas;
- recomendaciones para órdenes de trabajo;
- atención al cliente.

Cuando el usuario describa una falla, responde con:

1. Resumen del problema.
2. Posibles causas.
3. Pruebas recomendadas.
4. Nivel de urgencia.
5. Recomendación final.

Nunca confirmes que una pieza está dañada sin inspección o pruebas.

Cuando exista un riesgo de seguridad, indica que el vehículo no debería
circular hasta ser revisado.

Si faltan datos, solicita marca, modelo, año, kilometraje, motor,
síntomas y códigos de falla.

No inventes datos de clientes, vehículos, citas ni órdenes del sistema.
"""


# =========================================================
# HISTORIAL DEL CHAT
# =========================================================

if "historial_ia" not in st.session_state:
    st.session_state.historial_ia = [
        {
            "role": "assistant",
            "content": (
                "Hola. Soy el asistente IA del taller Doctor Fierros. "
                "Describe el vehículo y la consulta que deseas realizar."
            ),
        }
    ]


# =========================================================
# BOTÓN PARA LIMPIAR
# =========================================================

if st.button("🗑️ Limpiar conversación"):
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


# =========================================================
# MOSTRAR MENSAJES
# =========================================================

for mensaje in st.session_state.historial_ia:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])


# =========================================================
# RECIBIR PREGUNTA
# =========================================================

pregunta = st.chat_input(
    "Escribe aquí tu consulta automotriz..."
)

if pregunta:
    st.session_state.historial_ia.append(
        {
            "role": "user",
            "content": pregunta,
        }
    )

    with st.chat_message("user"):
        st.markdown(pregunta)

    mensajes_api = [
        {
            "role": "system",
            "content": INSTRUCCIONES,
        }
    ]

    mensajes_api.extend(
        st.session_state.historial_ia[-12:]
    )

    with st.chat_message("assistant"):
        with st.spinner("Analizando la consulta..."):
            try:
                respuesta = cliente_ia.chat.completions.create(
                    model="openrouter/free",
                    messages=mensajes_api,
                    temperature=0.3,
                    max_tokens=800,
                )

                texto = respuesta.choices[0].message.content

                if not texto:
                    texto = (
                        "El modelo no produjo una respuesta. "
                        "Intenta nuevamente."
                    )

            except Exception as error:
                detalle = str(error)

                if "401" in detalle:
                    texto = (
                        "La clave de OpenRouter no es válida o no está "
                        "configurada correctamente."
                    )

                elif "429" in detalle:
                    texto = (
                        "El servicio gratuito alcanzó temporalmente su "
                        "límite. Espera unos minutos e intenta nuevamente."
                    )

                else:
                    texto = (
                        "No fue posible obtener una respuesta de la IA.\n\n"
                        f"Detalle técnico: {detalle}"
                    )

        st.markdown(texto)

    st.session_state.historial_ia.append(
        {
            "role": "assistant",
            "content": texto,
        }
    )