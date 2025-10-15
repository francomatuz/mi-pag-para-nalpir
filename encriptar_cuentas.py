import csv
import requests
import json
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3

# Suprimir warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
MAX_WORKERS = 20  # Número de threads paralelos (ajustar según necesidad)  



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


def encriptar_cuenta_worker(registro: Dict[str, str]) -> Dict[str, str]:
    """Worker que encripta una cuenta (para usar en paralelo)"""
    cuenta = registro['cuenta']
    cod = registro['cod']

    cuenta_encriptada = encriptar_cuenta(cuenta, cod)

    return {
        'cuenta': cuenta,
        'cuenta_encriptada': cuenta_encriptada,
        'nombre': registro['nombre'],
        'dni': registro['dni'],
        'cod': cod
    }


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
        response = requests.post(API_URL, headers=HEADERS, json=body, timeout=10, verify=False)
        response.raise_for_status()

        data = response.json()

        # DEBUG: Descomentar para ver respuesta completa
        print(f"DEBUG Cuenta {cuenta}: {json.dumps(data, indent=2)}")

        cuenta_encriptada = data["DFHCOMMAREA"]["WS_ENC_FIELDS"]["WS_ENC_ACCT"]

        return cuenta_encriptada

    except Exception as e:
        if reintentos < MAX_REINTENTOS:
            time.sleep(0.5)
            return encriptar_cuenta(cuenta, cod, reintentos + 1)
        else:
            print(f" ✗ FALLO cuenta {cuenta}: {str(e)[:50]}")
            return "ERROR_ENCRIPTACION"


def procesar_cuentas(cuentas: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Procesa todas las cuentas y las encripta EN PARALELO"""

    resultados = []
    total = len(cuentas)
    procesados = 0

    print(f"\nIniciando encriptación de {total} cuentas...")
    print(f"Usando {MAX_WORKERS} threads en paralelo")
    print("=" * 60)

    inicio = time.time()

    # Procesar en paralelo con ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Enviar todas las tareas
        futures = {executor.submit(encriptar_cuenta_worker, registro): registro for registro in cuentas}

        # Ir recolectando resultados a medida que terminan
        for future in as_completed(futures):
            resultado = future.result()
            resultados.append(resultado)
            procesados += 1

            # Mostrar progreso cada 100 registros
            if procesados % 100 == 0 or procesados == total:
                porcentaje = (procesados / total) * 100
                transcurrido = time.time() - inicio
                velocidad = procesados / transcurrido if transcurrido > 0 else 0
                tiempo_restante = (total - procesados) / velocidad if velocidad > 0 else 0

                print(f"Procesados: {procesados}/{total} ({porcentaje:.1f}%) | "
                      f"Velocidad: {velocidad:.0f} cuentas/seg | "
                      f"Restante: {tiempo_restante/60:.1f} min")

            # Guardar cada BATCH_SIZE registros (por seguridad)
            if procesados % BATCH_SIZE == 0:
                guardar_resultados(resultados, ARCHIVO_SALIDA, modo='parcial')

    print("=" * 60)
    print(f"✓ Encriptación completada en {(time.time() - inicio)/60:.1f} minutos!")

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
