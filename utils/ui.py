import streamlit as st


def aplicar_estilos():
    st.markdown(
        """
        <style>
        /* =====================================================
           CONFIGURACIÓN GENERAL
        ===================================================== */

        .stApp {
            background:
                radial-gradient(
                    circle at top right,
                    rgba(37, 99, 235, 0.08),
                    transparent 30%
                ),
                #f4f7fb;
        }

        .block-container {
            max-width: 1450px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            padding-left: 2.2rem;
            padding-right: 2.2rem;
        }

        html,
        body,
        [class*="css"] {
            font-family:
                Inter,
                "Segoe UI",
                Arial,
                sans-serif;
        }

        h1,
        h2,
        h3,
        h4 {
            color: #172033;
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: 2rem !important;
        }

        p {
            color: #526071;
        }

        /* =====================================================
           MENÚ LATERAL
        ===================================================== */

        section[data-testid="stSidebar"] {
            background:
                linear-gradient(
                    180deg,
                    #0f172a 0%,
                    #172554 100%
                );
            border-right: none;
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.2rem;
        }

        section[data-testid="stSidebar"] * {
            color: #f8fafc;
        }

        section[data-testid="stSidebar"] a {
            border-radius: 10px;
            margin: 4px 8px;
            transition: all 0.2s ease;
        }

        section[data-testid="stSidebar"] a:hover {
            background: rgba(255, 255, 255, 0.12);
            transform: translateX(3px);
        }

        section[data-testid="stSidebar"]
        [data-testid="stSidebarNavLink"][aria-current="page"] {
            background:
                linear-gradient(
                    90deg,
                    #2563eb,
                    #3b82f6
                );
            box-shadow:
                0 8px 20px rgba(37, 99, 235, 0.28);
        }

        /* =====================================================
           TARJETAS DE MÉTRICAS
        ===================================================== */

        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 18px 20px;
            box-shadow:
                0 8px 25px rgba(15, 23, 42, 0.06);
            transition:
                transform 0.2s ease,
                box-shadow 0.2s ease;
        }

        div[data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            box-shadow:
                0 14px 30px rgba(15, 23, 42, 0.11);
        }

        div[data-testid="stMetricLabel"] {
            font-weight: 600;
            color: #64748b;
        }

        div[data-testid="stMetricValue"] {
            color: #1d4ed8;
            font-weight: 800;
        }

        /* =====================================================
           CONTENEDORES, FORMULARIOS Y EXPANDERS
        ===================================================== */

        div[data-testid="stForm"],
        div[data-testid="stExpander"] {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            box-shadow:
                0 8px 25px rgba(15, 23, 42, 0.05);
        }

        div[data-testid="stExpander"] details {
            border-radius: 16px;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 16px;
        }

        /* =====================================================
           CAMPOS DE ENTRADA
        ===================================================== */

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] > div {
            border-radius: 10px;
            border-color: #dbe3ee;
            background: #ffffff;
        }

        div[data-baseweb="input"] > div:focus-within,
        div[data-baseweb="select"] > div:focus-within,
        div[data-baseweb="textarea"] > div:focus-within {
            border-color: #2563eb;
            box-shadow:
                0 0 0 3px rgba(37, 99, 235, 0.12);
        }

        label[data-testid="stWidgetLabel"] p {
            color: #334155;
            font-weight: 600;
        }

        /* =====================================================
           BOTONES
        ===================================================== */

        div.stButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            min-height: 42px;
            border-radius: 10px;
            border: none;
            font-weight: 700;
            transition:
                transform 0.2s ease,
                box-shadow 0.2s ease;
        }

        div.stButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"]
        > button[kind="primary"] {
            background:
                linear-gradient(
                    90deg,
                    #1d4ed8,
                    #3b82f6
                );
            color: #ffffff;
            box-shadow:
                0 7px 18px rgba(37, 99, 235, 0.24);
        }

        div.stButton > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-2px);
        }

        div.stButton > button[kind="secondary"] {
            border: 1px solid #cbd5e1;
            background: #ffffff;
            color: #334155;
        }

        /* =====================================================
           TABLAS
        ===================================================== */

        div[data-testid="stDataFrame"] {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 8px;
            box-shadow:
                0 8px 25px rgba(15, 23, 42, 0.05);
            overflow: hidden;
        }

        /* =====================================================
           MENSAJES
        ===================================================== */

        div[data-testid="stAlert"] {
            border-radius: 12px;
            border: none;
        }

        /* =====================================================
           PESTAÑAS
        ===================================================== */

        button[data-baseweb="tab"] {
            border-radius: 9px 9px 0 0;
            font-weight: 700;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: #2563eb;
        }

        /* =====================================================
           DIVISORES
        ===================================================== */

        hr {
            border: none;
            border-top: 1px solid #e2e8f0;
            margin-top: 1.7rem;
            margin-bottom: 1.7rem;
        }

        /* =====================================================
           OCULTAR ELEMENTOS INNECESARIOS
        ===================================================== */

        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        div[data-testid="stStatusWidget"] {
            visibility: hidden;
        }

        /* =====================================================
           DISEÑO RESPONSIVE
        ===================================================== */

        @media (max-width: 900px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            h1 {
                font-size: 1.6rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def encabezado_modulo(
    titulo: str,
    descripcion: str,
    icono: str = "🚘",
):
    st.markdown(
        f"""
        <div style="
            background:
                linear-gradient(
                    110deg,
                    #172554 0%,
                    #1d4ed8 55%,
                    #3b82f6 100%
                );
            padding: 25px 28px;
            border-radius: 18px;
            margin-bottom: 24px;
            box-shadow:
                0 12px 30px rgba(30, 64, 175, 0.22);
        ">
            <div style="
                display: flex;
                align-items: center;
                gap: 16px;
            ">
                <div style="
                    width: 55px;
                    height: 55px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(255, 255, 255, 0.16);
                    border: 1px solid rgba(255, 255, 255, 0.20);
                    border-radius: 15px;
                    font-size: 29px;
                ">
                    {icono}
                </div>

                <div>
                    <div style="
                        color: white;
                        font-size: 27px;
                        font-weight: 800;
                        line-height: 1.2;
                    ">
                        {titulo}
                    </div>

                    <div style="
                        color: rgba(255, 255, 255, 0.82);
                        font-size: 14px;
                        margin-top: 6px;
                    ">
                        {descripcion}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def tarjeta_informativa(
    titulo: str,
    valor: str,
    icono: str,
    descripcion: str = "",
):
    st.markdown(
        f"""
        <div style="
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 19px;
            min-height: 135px;
            box-shadow:
                0 8px 22px rgba(15, 23, 42, 0.06);
        ">
            <div style="
                display: flex;
                align-items: center;
                justify-content: space-between;
            ">
                <div style="
                    color: #64748b;
                    font-size: 13px;
                    font-weight: 700;
                    text-transform: uppercase;
                ">
                    {titulo}
                </div>

                <div style="
                    font-size: 25px;
                    background: #eff6ff;
                    padding: 8px 11px;
                    border-radius: 11px;
                ">
                    {icono}
                </div>
            </div>

            <div style="
                color: #1d4ed8;
                font-size: 29px;
                font-weight: 800;
                margin-top: 9px;
            ">
                {valor}
            </div>

            <div style="
                color: #94a3b8;
                font-size: 12px;
                margin-top: 4px;
            ">
                {descripcion}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )