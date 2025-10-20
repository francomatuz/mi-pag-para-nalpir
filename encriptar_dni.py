import csv
import requests
import json
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3

# Suprimir warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# CONFIGURACION - COMPLETAR VALORES REALES
API_URL_BASE = "https://[DOMINIO]/api"  # Completar con dominio real

HEADERS_BASE = {
    'Content-Type': 'application/json',
    'X-ClientID': 'clientId',  # Completar valor real
    'requestId': 'requestId',  # Completar valor real
    'security-context': 'securityContext'  # Completar valor real
}

ARCHIVO_ENTRADA = "cuentas_encriptadas.txt"
ARCHIVO_SALIDA = "dni_encriptados.txt"

BATCH_SIZE = 500
MAX_REINTENTOS = 3
MAX_WORKERS = 10

# Entidades a procesar (las mismas que para encriptar cuentas)
ENTIDADES_PERMITIDAS = {
    '002', '004', '005', '007', '015', '024', '027', '031', '035', '036', '040', '042', '048',
    '066', '069', '071', '074', '084', '090', '092', '093', '101', '106', '119', '129', '131',
    '139', '140', '154', '160', '161', '163', '165', '167', '168', '170', '173', '176', '187',
    '196', '218', '227', '234', '242', '243', '244', '247', '270'
}


def leer_cuentas_encriptadas(archivo: str) -> List[Dict[str, str]]:
    """Lee el archivo con cuentas encriptadas"""
    registros = []
    excluidos = 0

    print(f"Leyendo archivo {archivo}...")

    with open(archivo, 'r', encoding='ISO-8859-1') as f:
        reader = csv.DictReader(f, delimiter=';', quotechar='"')

        for row in reader:
            cod = row['cod']

            # Filtrar solo entidades permitidas y que tengan cuenta encriptada
            if cod in ENTIDADES_PERMITIDAS and row.get('cuenta_encriptada'):
                registros.append({
                    'cuenta': row['cuenta'],
                    'cuenta_encriptada': row['cuenta_encriptada'],
                    'nombre': row['nombre'],
                    'dni': row['dni'],
                    'cod': row['cod'],
                    'mail': row.get('mail', '')  # Agregar mail si existe
                })
            else:
                excluidos += 1

    print(f"{len(registros)} registros a procesar (excluidos: {excluidos})")
    return registros


def encriptar_dni(cuenta_encriptada: str, dni: str, mail: str, cod: str, reintentos: int = 0) -> tuple:
    """Llama a la API para encriptar DNI. Retorna (success, error_msg)"""

    # Quitar ceros adelante del COD para la URL
    cod_sin_ceros = cod.lstrip('0') or '0'

    # Construir URL con COD sin ceros
    url = f"{API_URL_BASE}/userEntity={cod_sin_ceros}"

    # Construir username con COD completo (con ceros)
    headers = HEADERS_BASE.copy()
    headers['username'] = f"E{cod}WSDE"

    payload = json.dumps({
        "account": {
            "accountNumber": cuenta_encriptada,
            "additional": 0
        },
        "email": mail,
        "encryptionPassword": dni
    })

    try:
        response = requests.request("PUT", url, headers=headers, data=payload, verify=False, timeout=10)

        # Si la respuesta es 200 OK, es exitoso
        if response.status_code == 200:
            return (True, None)

        # Si hay error, intentar parsear el mensaje
        try:
            data = response.json()
            error_msg = data.get("errorResponse", {}).get("description", f"HTTP {response.status_code}")
            return (False, error_msg)
        except:
            return (False, f"HTTP {response.status_code}")

    except Exception as e:
        if reintentos < MAX_REINTENTOS:
            time.sleep(0.5)
            return encriptar_dni(cuenta_encriptada, dni, mail, cod, reintentos + 1)
        else:
            return (False, f"ERROR_EXCEPTION: {str(e)[:50]}")


def encriptar_dni_worker(registro: Dict[str, str]) -> Dict[str, str]:
    """Worker que encripta un DNI (para usar en paralelo)"""
    cuenta_encriptada = registro['cuenta_encriptada']
    dni = registro['dni']
    mail = registro['mail']
    cod = registro['cod']

    success, error_msg = encriptar_dni(cuenta_encriptada, dni, mail, cod)

    return {
        'cuenta': registro['cuenta'],
        'cuenta_encriptada': cuenta_encriptada,
        'nombre': registro['nombre'],
        'dni': dni,
        'mail': mail,
        'cod': cod,
        'dni_encriptado': success,
        'error': error_msg
    }


def procesar_registros(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Procesa todos los registros y encripta DNIs EN PARALELO"""

    resultados = []
    total = len(registros)
    procesados = 0

    print(f"\nIniciando encriptacion de {total} DNIs...")
    print(f"Usando {MAX_WORKERS} threads en paralelo")
    print("=" * 60)

    inicio = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(encriptar_dni_worker, registro): registro for registro in registros}

        for future in as_completed(futures):
            resultado = future.result()
            resultados.append(resultado)
            procesados += 1

            if procesados % 100 == 0 or procesados == total:
                porcentaje = (procesados / total) * 100
                transcurrido = time.time() - inicio
                velocidad = procesados / transcurrido if transcurrido > 0 else 0
                tiempo_restante = (total - procesados) / velocidad if velocidad > 0 else 0

                print(f"Procesados: {procesados}/{total} ({porcentaje:.1f}%) | "
                      f"Velocidad: {velocidad:.0f} registros/seg | "
                      f"Restante: {tiempo_restante/60:.1f} min")

            if procesados % BATCH_SIZE == 0:
                guardar_resultados(resultados, ARCHIVO_SALIDA, modo='parcial')

    print("=" * 60)
    print(f"Encriptacion completada en {(time.time() - inicio)/60:.1f} minutos!")

    return resultados


def guardar_resultados(resultados: List[Dict[str, str]], archivo: str, modo='final'):
    """Guarda los resultados en un archivo CSV"""

    with open(archivo, 'w', encoding='ISO-8859-1', newline='') as f:
        writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)

        writer.writerow(['cuenta', 'cuenta_encriptada', 'nombre', 'dni', 'mail', 'cod', 'dni_encriptado'])

        for r in resultados:
            writer.writerow([
                r['cuenta'],
                r['cuenta_encriptada'],
                r['nombre'],
                r['dni'],
                r['mail'],
                r['cod'],
                'SI' if r['dni_encriptado'] else 'NO'
            ])

    if modo == 'final':
        print(f"\nResultados guardados en: {archivo}")
    else:
        print(f"  Guardado parcial: {len(resultados)} registros")


def guardar_errores(resultados: List[Dict[str, str]], archivo: str):
    """Guarda solo los registros con error"""

    errores = [r for r in resultados if r.get('error')]

    if not errores:
        print("No hay errores para guardar")
        return

    with open(archivo, 'w', encoding='ISO-8859-1', newline='') as f:
        writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)

        writer.writerow(['cuenta', 'nombre', 'dni', 'mail', 'cod', 'tipo_error'])

        for r in errores:
            writer.writerow([
                r['cuenta'],
                r['nombre'],
                r['dni'],
                r['mail'],
                r['cod'],
                r['error']
            ])

    print(f"Archivo de errores guardado: {archivo} ({len(errores)} registros)")


def main():
    print("=" * 60)
    print("    SCRIPT DE ENCRIPTACION DE DNI")
    print("=" * 60)

    registros = leer_cuentas_encriptadas(ARCHIVO_ENTRADA)

    resultados = procesar_registros(registros)

    guardar_resultados(resultados, ARCHIVO_SALIDA, modo='final')

    guardar_errores(resultados, "dni_con_error.txt")

    exitosos = sum(1 for r in resultados if r['dni_encriptado'])
    con_error = sum(1 for r in resultados if r.get('error'))

    errores_por_tipo = {}
    for r in resultados:
        if r.get('error'):
            error_tipo = r['error']
            errores_por_tipo[error_tipo] = errores_por_tipo.get(error_tipo, 0) + 1

    print("\n" + "=" * 60)
    print("RESUMEN:")
    print(f"  Total procesados: {len(resultados)}")
    print(f"  DNI encriptados exitosamente: {exitosos}")
    print(f"  Con errores: {con_error}")

    if errores_por_tipo:
        print("\n  Errores por tipo:")
        for tipo, cantidad in sorted(errores_por_tipo.items(), key=lambda x: x[1], reverse=True):
            print(f"    - {tipo}: {cantidad}")

    print("=" * 60)


if __name__ == "__main__":
    main()
