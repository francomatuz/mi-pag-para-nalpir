import csv
from collections import Counter

def parsear_linea_csv(linea):
    """Parsea una línea CSV considerando comillas"""
    campos = []
    dentro_comillas = False
    campo_actual = []

    for char in linea:
        if char == '"':
            dentro_comillas = not dentro_comillas
        elif char == ';' and not dentro_comillas:
            campos.append(''.join(campo_actual))
            campo_actual = []
        else:
            campo_actual.append(char)

    campos.append(''.join(campo_actual))
    return campos


def contar_por_entidad(archivo):
    """Cuenta la cantidad de personas por COD en el archivo"""
    contador = Counter()
    total = 0

    print(f"\nLeyendo {archivo}...")

    with open(archivo, 'r', encoding='ISO-8859-1') as f:
        # Saltar header
        f.readline()

        for linea in f:
            campos = parsear_linea_csv(linea.strip())

            if len(campos) >= 3:
                cod = campos[2]  # El COD está en la tercera columna
                contador[cod] += 1
                total += 1

                if total % 100000 == 0:
                    print(f"  Procesados {total:,} registros...")

    print(f"  Total: {total:,} registros")
    print(f"  Entidades únicas: {len(contador)}")

    return contador, total


def main():
    print("=" * 80)
    print("COMPARADOR DE ARCHIVOS CON_DNI.TXT")
    print("=" * 80)

    archivo_viejo = input("Nombre del archivo VIEJO (ej: con_dni_viejo.txt): ").strip()
    archivo_nuevo = input("Nombre del archivo NUEVO (ej: con_dni.txt): ").strip()

    # Contar en ambos archivos
    contador_viejo, total_viejo = contar_por_entidad(archivo_viejo)
    contador_nuevo, total_nuevo = contar_por_entidad(archivo_nuevo)

    # Calcular diferencia total
    diferencia_total = total_nuevo - total_viejo

    print("\n" + "=" * 80)
    print("RESUMEN GENERAL:")
    print(f"  Archivo viejo: {total_viejo:,} registros")
    print(f"  Archivo nuevo: {total_nuevo:,} registros")
    print(f"  Diferencia: {diferencia_total:+,} registros")
    print("=" * 80)

    # Todas las entidades que aparecen en alguno de los dos archivos
    todas_entidades = sorted(set(contador_viejo.keys()) | set(contador_nuevo.keys()))

    # Calcular diferencias por entidad
    diferencias = []

    for cod in todas_entidades:
        cant_viejo = contador_viejo.get(cod, 0)
        cant_nuevo = contador_nuevo.get(cod, 0)
        diferencia = cant_nuevo - cant_viejo

        if diferencia != 0:
            diferencias.append({
                'cod': cod,
                'viejo': cant_viejo,
                'nuevo': cant_nuevo,
                'diferencia': diferencia
            })

    # Ordenar por diferencia (las que más perdieron primero)
    diferencias.sort(key=lambda x: x['diferencia'])

    print("\n=== ENTIDADES CON DIFERENCIAS ===\n")
    print(f"{'COD':<6} {'Viejo':>12} {'Nuevo':>12} {'Diferencia':>15} {'Cambio %':>12}")
    print("-" * 80)

    for d in diferencias:
        porcentaje = ((d['diferencia'] / d['viejo']) * 100) if d['viejo'] > 0 else 0
        print(f"{d['cod']:<6} {d['viejo']:>12,} {d['nuevo']:>12,} {d['diferencia']:>+15,} {porcentaje:>11.1f}%")

    # Resumen de las que más perdieron
    print("\n" + "=" * 80)
    print("TOP 10 ENTIDADES QUE MÁS PERDIERON REGISTROS:")
    print("-" * 80)

    perdieron = [d for d in diferencias if d['diferencia'] < 0][:10]

    if perdieron:
        for i, d in enumerate(perdieron, 1):
            print(f"{i}. COD {d['cod']}: {d['diferencia']:+,} registros ({d['viejo']:,} -> {d['nuevo']:,})")
    else:
        print("Ninguna entidad perdió registros")

    # Resumen de las que más ganaron
    print("\n" + "=" * 80)
    print("TOP 10 ENTIDADES QUE MÁS GANARON REGISTROS:")
    print("-" * 80)

    ganaron = [d for d in reversed(diferencias) if d['diferencia'] > 0][:10]

    if ganaron:
        for i, d in enumerate(ganaron, 1):
            print(f"{i}. COD {d['cod']}: {d['diferencia']:+,} registros ({d['viejo']:,} -> {d['nuevo']:,})")
    else:
        print("Ninguna entidad ganó registros")

    print("\n" + "=" * 80)

    # Guardar reporte en archivo
    with open("comparacion_con_dni_reporte.txt", 'w', encoding='utf-8') as f:
        f.write("REPORTE DE COMPARACIÓN CON_DNI.TXT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Archivo viejo: {archivo_viejo} ({total_viejo:,} registros)\n")
        f.write(f"Archivo nuevo: {archivo_nuevo} ({total_nuevo:,} registros)\n")
        f.write(f"Diferencia total: {diferencia_total:+,} registros\n\n")

        f.write("DETALLE POR ENTIDAD:\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'COD':<6} {'Viejo':>12} {'Nuevo':>12} {'Diferencia':>15} {'Cambio %':>12}\n")
        f.write("-" * 80 + "\n")

        for d in diferencias:
            porcentaje = ((d['diferencia'] / d['viejo']) * 100) if d['viejo'] > 0 else 0
            f.write(f"{d['cod']:<6} {d['viejo']:>12,} {d['nuevo']:>12,} {d['diferencia']:>+15,} {porcentaje:>11.1f}%\n")

    print("\nReporte guardado en: comparacion_con_dni_reporte.txt")


if __name__ == "__main__":
    main()
