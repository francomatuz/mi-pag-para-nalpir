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
    "Content-Type": "application/json"
}

ARCHIVO_ENTRADA = "todos_encontrados.txt"
ARCHIVO_SALIDA = "cuentas_encriptadas.txt"


BATCH_SIZE = 100
DELAY_ENTRE_REQUESTS = 0.1
MAX_REINTENTOS = 3
MAX_WORKERS = 1  # Número de threads paralelos (ajustar según necesidad)  



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

    print(f"{len(cuentas)} registros leidos")
    return cuentas


def encriptar_cuenta_worker(registro: Dict[str, str]) -> Dict[str, str]:
    """Worker que encripta una cuenta (para usar en paralelo)"""
    cuenta = registro['cuenta']
    cod = registro['cod']

    cuenta_encriptada, error_msg = encriptar_cuenta(cuenta, cod)

    return {
        'cuenta': cuenta,
        'cuenta_encriptada': cuenta_encriptada,
        'nombre': registro['nombre'],
        'dni': registro['dni'],
        'cod': cod,
        'error': error_msg
    }


def encriptar_cuenta(cuenta: str, cod: str, reintentos: int = 0) -> tuple:
    """Llama a la API para encriptar una cuenta. Retorna (cuenta_encriptada, error_msg)"""

    # DEBUG: Ver qué valores llegan
    # print(f"DEBUG INPUT - Cuenta: '{cuenta}' | COD: '{cod}'")

    # Crear payload exactamente como Postman
    payload = json.dumps({
        "DFHCOMMAREA": {
            "WS_CLIENT_ID": cod,
            "WS_INP_ENV": "",
            "WS_INP_FIELDS": {
                "WS_INP_ACCT": cuenta,
                "WS_INP_CARD_NBR": "",
                "WS_INP_CARD_NAME": "",
                "WS_INP_CVV": "",
                "WS_INP_EXPDT": ""
            }
        }
    })

    # DEBUG: Comparar payloads
    # print(f"PAYLOAD LENGTH: {len(payload)}")
    # print(f"PAYLOAD: {payload}")
    # print(f"CUENTA TIPO: {type(cuenta)} - VALOR: '{cuenta}'")

    try:
        response = requests.request("POST", API_URL, headers=HEADERS, data=payload, verify=False)
        response.raise_for_status()

        data = response.json()

        # DEBUG: Descomentar para ver respuesta completa
        # print(f"DEBUG Cuenta {cuenta}: {json.dumps(data, indent=2)}")

        # Verificar si la API devolvió error
        ws_svc_return = data.get("DFHCOMMAREA", {}).get("WS_SVC_RETURN", "")
        ws_error_msg = data.get("DFHCOMMAREA", {}).get("WS_ERROR_MSG", "")

        if ws_svc_return == "F" or ws_error_msg:
            error_tipo = ws_error_msg if ws_error_msg else "ERROR_DESCONOCIDO"
            return ("", error_tipo)

        cuenta_encriptada = data["DFHCOMMAREA"]["WS_ENC_FIELDS"]["WS_ENC_ACCT"]
        return (cuenta_encriptada, None)

    except Exception as e:
        if reintentos < MAX_REINTENTOS:
            time.sleep(0.5)
            return encriptar_cuenta(cuenta, cod, reintentos + 1)
        else:
            print(f"FALLO cuenta {cuenta}: {str(e)[:50]}")
            return ("", f"ERROR_EXCEPTION: {str(e)[:50]}")


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
    print(f"Encriptacion completada en {(time.time() - inicio)/60:.1f} minutos!")

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
        print(f"\nResultados guardados en: {archivo}")
    else:
        print(f"  Guardado parcial: {len(resultados)} registros")


def guardar_errores(resultados: List[Dict[str, str]], archivo: str):
    """Guarda solo las cuentas con error en un archivo separado"""

    errores = [r for r in resultados if r.get('error')]

    if not errores:
        print("No hay errores para guardar")
        return

    with open(archivo, 'w', encoding='ISO-8859-1', newline='') as f:
        writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)

        # Header
        writer.writerow(['cuenta', 'nombre', 'dni', 'cod', 'tipo_error'])

        # Datos
        for r in errores:
            writer.writerow([
                r['cuenta'],
                r['nombre'],
                r['dni'],
                r['cod'],
                r['error']
            ])

    print(f"Archivo de errores guardado: {archivo} ({len(errores)} registros)")


# ==================== MAIN ====================

def main():
    print("=" * 60)
    print("    SCRIPT DE ENCRIPTACIÓN DE CUENTAS")
    print("=" * 60)

    # Leer archivo
    cuentas = leer_cuentas(ARCHIVO_ENTRADA)

    # DEBUG: Procesar solo las primeras 10 cuentas
    # cuentas = cuentas[:10]
    # print(f"MODO DEBUG: Procesando solo {len(cuentas)} cuentas\n")

    # Procesar y encriptar
    resultados = procesar_cuentas(cuentas)

    # Guardar resultados finales
    guardar_resultados(resultados, ARCHIVO_SALIDA, modo='final')

    # Guardar archivo de errores
    guardar_errores(resultados, "cuentas_con_error.txt")

    # Contar tipos de errores
    exitosos = sum(1 for r in resultados if not r.get('error'))
    con_error = sum(1 for r in resultados if r.get('error'))

    # Agrupar por tipo de error
    errores_por_tipo = {}
    for r in resultados:
        if r.get('error'):
            error_tipo = r['error']
            errores_por_tipo[error_tipo] = errores_por_tipo.get(error_tipo, 0) + 1

    print("\n" + "=" * 60)
    print("RESUMEN:")
    print(f"  Total procesados: {len(resultados)}")
    print(f"  Exitosos: {exitosos}")
    print(f"  Con errores: {con_error}")

    if errores_por_tipo:
        print("\n  Errores por tipo:")
        for tipo, cantidad in sorted(errores_por_tipo.items(), key=lambda x: x[1], reverse=True):
            print(f"    - {tipo}: {cantidad}")

    print("=" * 60)


if __name__ == "__main__":
    main()
