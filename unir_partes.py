import csv

print("=" * 60)
print("UNIENDO ARCHIVOS ENCRIPTADOS")
print("=" * 60)

archivo_salida = "cuentas_encriptadas.txt"
num_partes = 10

# Leer el header del primer archivo
with open("cuentas_encriptadas_parte1.txt", 'r', encoding='ISO-8859-1') as f:
    header = f.readline()

# Crear archivo de salida
with open(archivo_salida, 'w', encoding='ISO-8859-1') as salida:
    # Escribir header
    salida.write(header)

    total_registros = 0

    # Procesar cada parte
    for i in range(1, num_partes + 1):
        archivo_parte = f"cuentas_encriptadas_parte{i}.txt"

        try:
            with open(archivo_parte, 'r', encoding='ISO-8859-1') as f:
                f.readline()  # Saltar header

                registros = 0
                for linea in f:
                    salida.write(linea)
                    registros += 1

                total_registros += registros
                print(f"Parte {i}: {registros:,} registros agregados")

        except FileNotFoundError:
            print(f"ADVERTENCIA: No se encontró {archivo_parte}")

print("=" * 60)
print(f"Archivo unificado: {archivo_salida}")
print(f"Total registros: {total_registros:,}")
print("=" * 60)
