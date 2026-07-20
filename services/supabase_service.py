import os
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client


# =========================================================
# CONEXIÓN CON SUPABASE
# =========================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = (
    os.getenv("SUPABASE_KEY")
    or os.getenv("SUPABASE_ANON_KEY")
)

if not SUPABASE_URL:
    raise ValueError(
        "No se encontró SUPABASE_URL en el archivo .env."
    )

if not SUPABASE_KEY:
    raise ValueError(
        "No se encontró SUPABASE_KEY o SUPABASE_ANON_KEY "
        "en el archivo .env."
    )

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)


# =========================================================
# FUNCIÓN AUXILIAR
# =========================================================

def _obtener_datos(respuesta: Any) -> list[dict]:
    """
    Devuelve una lista segura con los datos recibidos
    desde Supabase.
    """
    datos = getattr(respuesta, "data", None)

    if datos is None:
        return []

    return datos


# =========================================================
# CLIENTES
# =========================================================

def obtener_clientes() -> list[dict]:
    respuesta = (
        supabase.table("clientes")
        .select("*")
        .order("id", desc=False)
        .execute()
    )

    return _obtener_datos(respuesta)


def crear_cliente(datos: dict) -> list[dict]:
    respuesta = (
        supabase.table("clientes")
        .insert(datos)
        .execute()
    )

    return _obtener_datos(respuesta)


def actualizar_cliente(
    cliente_id: int,
    datos: dict,
) -> list[dict]:
    respuesta = (
        supabase.table("clientes")
        .update(datos)
        .eq("id", cliente_id)
        .execute()
    )

    return _obtener_datos(respuesta)


# =========================================================
# VEHÍCULOS
# =========================================================

def obtener_vehiculos() -> list[dict]:
    respuesta = (
        supabase.table("vehiculos")
        .select(
            """
            *,
            clientes (
                id,
                cedula,
                nombres,
                apellidos,
                telefono,
                correo
            )
            """
        )
        .order("id", desc=False)
        .execute()
    )

    return _obtener_datos(respuesta)


def crear_vehiculo(datos: dict) -> list[dict]:
    respuesta = (
        supabase.table("vehiculos")
        .insert(datos)
        .execute()
    )

    return _obtener_datos(respuesta)


def actualizar_vehiculo(
    vehiculo_id: int,
    datos: dict,
) -> list[dict]:
    respuesta = (
        supabase.table("vehiculos")
        .update(datos)
        .eq("id", vehiculo_id)
        .execute()
    )

    return _obtener_datos(respuesta)


# =========================================================
# TÉCNICOS
# =========================================================

def obtener_tecnicos() -> list[dict]:
    respuesta = (
        supabase.table("tecnicos")
        .select("*")
        .order("id", desc=False)
        .execute()
    )

    return _obtener_datos(respuesta)


def crear_tecnico(datos: dict) -> list[dict]:
    respuesta = (
        supabase.table("tecnicos")
        .insert(datos)
        .execute()
    )

    return _obtener_datos(respuesta)


def actualizar_tecnico(
    tecnico_id: int,
    datos: dict,
) -> list[dict]:
    respuesta = (
        supabase.table("tecnicos")
        .update(datos)
        .eq("id", tecnico_id)
        .execute()
    )

    return _obtener_datos(respuesta)


# =========================================================
# ÓRDENES DE TRABAJO
# =========================================================

def obtener_ordenes_trabajo() -> list[dict]:
    respuesta = (
        supabase.table("ordenes_trabajo")
        .select(
            """
            *,
            vehiculos (
                id,
                placa,
                marca,
                modelo,
                anio,
                clientes (
                    id,
                    cedula,
                    nombres,
                    apellidos,
                    telefono,
                    correo
                )
            ),
            tecnicos (
                id,
                cedula,
                nombres,
                apellidos,
                especialidad,
                nivel,
                activo
            )
            """
        )
        .order("id", desc=True)
        .execute()
    )

    return _obtener_datos(respuesta)


def crear_orden_trabajo(datos: dict) -> list[dict]:
    respuesta = (
        supabase.table("ordenes_trabajo")
        .insert(datos)
        .execute()
    )

    return _obtener_datos(respuesta)


def actualizar_orden_trabajo(
    orden_id: int,
    datos: dict,
) -> list[dict]:
    respuesta = (
        supabase.table("ordenes_trabajo")
        .update(datos)
        .eq("id", orden_id)
        .execute()
    )

    return _obtener_datos(respuesta)