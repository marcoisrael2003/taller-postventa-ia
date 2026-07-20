import os

from dotenv import load_dotenv
from supabase import Client, create_client


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Faltan SUPABASE_URL o SUPABASE_KEY en el archivo .env"
    )

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)


# ---------------------------------------------------------
# CLIENTES
# ---------------------------------------------------------

def obtener_clientes() -> list[dict]:
    respuesta = (
        supabase.table("clientes")
        .select("*")
        .order("id", desc=False)
        .execute()
    )

    return respuesta.data


def crear_cliente(datos: dict) -> list[dict]:
    respuesta = (
        supabase.table("clientes")
        .insert(datos)
        .execute()
    )

    return respuesta.data


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

    return respuesta.data


# ---------------------------------------------------------
# VEHÍCULOS
# ---------------------------------------------------------

def obtener_vehiculos() -> list[dict]:
    respuesta = (
        supabase.table("vehiculos")
        .select(
            """
            id,
            cliente_id,
            placa,
            marca,
            modelo,
            anio,
            color,
            kilometraje,
            vin,
            activo,
            fecha_registro,
            clientes (
                cedula,
                nombres,
                apellidos
            )
            """
        )
        .order("id", desc=False)
        .execute()
    )

    return respuesta.data


def crear_vehiculo(datos: dict) -> list[dict]:
    respuesta = (
        supabase.table("vehiculos")
        .insert(datos)
        .execute()
    )

    return respuesta.data


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

    return respuesta.data