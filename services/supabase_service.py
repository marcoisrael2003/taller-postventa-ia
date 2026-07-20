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


# =========================================================
# VEHÍCULOS
# =========================================================

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


# =========================================================
# ÓRDENES DE TRABAJO
# =========================================================

def obtener_ordenes_trabajo() -> list[dict]:
    respuesta = (
        supabase.table("ordenes_trabajo")
        .select(
            """
            id,
            vehiculo_id,
            fecha_ingreso,
            motivo_ingreso,
            diagnostico,
            estado,
            observaciones,
            fecha_estimada_entrega,
            fecha_entrega_real,
            costo_estimado,
            costo_final,
            kilometraje_ingreso,
            activo,
            fecha_creacion,
            vehiculos (
                placa,
                marca,
                modelo,
                cliente_id,
                clientes (
                    cedula,
                    nombres,
                    apellidos
                )
            )
            """
        )
        .order("id", desc=True)
        .execute()
    )

    return respuesta.data


def crear_orden_trabajo(datos: dict) -> list[dict]:
    respuesta = (
        supabase.table("ordenes_trabajo")
        .insert(datos)
        .execute()
    )

    return respuesta.data


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

    return respuesta.data