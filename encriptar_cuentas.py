import csv
import requests
import json
import time
from typing import List, Dict


API_URL = ""

HEADERS = {
    "Cache-Control": "no-cache",
    "Content-Type": "application/json",
    "User-Agent": "PostmanRuntime/7.39.0",
    "Accept": "*/*",
    "Accept-Encoding": "",
    "Connection": "keep-alive"
}

ARCHIVO_ENTRADA = "todos_encontrados.txt"
ARCHIVO_SALIDA = "cuentas_encriptadas.txt"


BATCH_SIZE = 100  
DELAY_ENTRE_REQUESTS = 0.1  
MAX_REINTENTOS = 3  



def leer_cuentas(archivo: str) -> List[Dict[str, str]]:
    """Lee el archivo todos_encontrados.txt y extrae cuenta y cod"""
    cuentas = []

    print(f"Leyendo archivo {archivo}...")

    with open(archivo, 'r', encoding='ISO-8859-1') as f:
        reader = csv.DictReader(f, delimiter=';', quotechar='"')

        for row in reader:
            cuentas.append({
                'cuenta': row['cuenta'],
                'nombre': row['nombre'],
                'dni': row['dni'],
                'cod': row['cod']
            })

    print(f"✓ {len(cuentas)} registros leídos")
    return cuentas


def encriptar_cuenta(cuenta: str, cod: str, reintentos: int = 0) -> str:
    """Llama a la API para encriptar una cuenta"""

    body = {
        "DFHCOMMAREA": {
            "WS_CLIENT_ID": cod,
            "WS_INP_ENV": "",
            "WS_ENC_FIELDS": {
                "WS_ENC_ACCT": cuenta,
                "WS_INP": "",
                "WS_INP2": "",
                "WS_INP3": "",
                "WS_INP4": ""
            }
        }
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=body, timeout=10)
        response.raise_for_status()

        data = response.json()
        cuenta_encriptada = data["DFHCOMMAREA"]["WS_ENC_FIELDS"]["WS_ENC_ACCT"]

        return cuenta_encriptada

    except Exception as e:
        if reintentos < MAX_REINTENTOS:
            print(f" Error encriptando cuenta {cuenta} (intento {reintentos + 1}/{MAX_REINTENTOS}): {e}")
            time.sleep(1)
            return encriptar_cuenta(cuenta, cod, reintentos + 1)
        else:
            print(f" FALLO después de {MAX_REINTENTOS} intentos: cuenta {cuenta}")
            return "ERROR_ENCRIPTACION"


def procesar_cuentas(cuentas: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Procesa todas las cuentas y las encripta"""

    resultados = []
    total = len(cuentas)

    print(f"\nIniciando encriptación de {total} cuentas...")
    print("=" * 60)

    for i, registro in enumerate(cuentas, 1):
        cuenta = registro['cuenta']
        cod = registro['cod']

        # Encriptar cuenta
        cuenta_encriptada = encriptar_cuenta(cuenta, cod)

        # Guardar resultado
        resultados.append({
            'cuenta': cuenta,
            'cuenta_encriptada': cuenta_encriptada,
            'nombre': registro['nombre'],
            'dni': registro['dni'],
            'cod': cod
        })

        # Mostrar progreso
        if i % 10 == 0 or i == total:
            porcentaje = (i / total) * 100
            print(f"Procesados: {i}/{total} ({porcentaje:.1f}%) - Cuenta: {cuenta} → {cuenta_encriptada[:20]}...")

        # Guardar cada BATCH_SIZE registros (por seguridad)
        if i % BATCH_SIZE == 0:
            guardar_resultados(resultados, ARCHIVO_SALIDA, modo='parcial')

        # Delay entre requests
        time.sleep(DELAY_ENTRE_REQUESTS)

    print("=" * 60)
    print(f"Encriptación completada!")

    return resultados


def guardar_resultados(resultados: List[Dict[str, str]], archivo: str, modo='final'):
    """Guarda los resultados en un archivo CSV"""

    with open(archivo, 'w', encoding='ISO-8859-1', newline='') as f:
        writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)

        # Header
        writer.writerow(['cuenta', 'cuenta_encriptada', 'nombre', 'dni', 'cod'])

        # Datos
        for r in resultados:
            writer.writerow([
                r['cuenta'],
                r['cuenta_encriptada'],
                r['nombre'],
                r['dni'],
                r['cod']
            ])

    if modo == 'final':
        print(f"\n Resultados guardados en: {archivo}")
    else:
        print(f"  Guardado parcial: {len(resultados)} registros")


# ==================== MAIN ====================

def main():
    print("=" * 60)
    print("    SCRIPT DE ENCRIPTACIÓN DE CUENTAS")
    print("=" * 60)

    # Leer archivo
    cuentas = leer_cuentas(ARCHIVO_ENTRADA)

    # Procesar y encriptar
    resultados = procesar_cuentas(cuentas)

    # Guardar resultados finales
    guardar_resultados(resultados, ARCHIVO_SALIDA, modo='final')

  
    errores = sum(1 for r in resultados if r['cuenta_encriptada'] == 'ERROR_ENCRIPTACION')
    exitosos = len(resultados) - errores

    print("\n" + "=" * 60)
    print("RESUMEN:")
    print(f"  Total procesados: {len(resultados)}")
    print(f"  Exitosos: {exitosos}")
    print(f"  Errores: {errores}")
    print("=" * 60)


if __name__ == "__main__":
    main()
