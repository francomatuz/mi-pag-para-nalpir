import csv

# Configuracion
ARCHIVO_ENTRADA = "todos_encontrados.txt"
NUM_PARTES = 5

print(f"Dividiendo {ARCHIVO_ENTRADA} en {NUM_PARTES} partes...")

# Leer todas las lineas
with open(ARCHIVO_ENTRADA, 'r', encoding='ISO-8859-1') as f:
    reader = csv.reader(f, delimiter=';', quotechar='"')
    header = next(reader)
    lineas = list(reader)

total = len(lineas)
por_parte = total // NUM_PARTES
print(f"Total registros: {total}")
print(f"Por archivo: ~{por_parte}")

# Dividir en partes
for i in range(NUM_PARTES):
    inicio = i * por_parte
    if i == NUM_PARTES - 1:
        # Ultima parte toma todo lo que queda
        fin = total
    else:
        fin = (i + 1) * por_parte

    parte = lineas[inicio:fin]

    nombre_archivo = f"todos_encontrados_parte{i+1}.txt"

    with open(nombre_archivo, 'w', encoding='ISO-8859-1', newline='') as f:
        writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(header)
        writer.writerows(parte)

    print(f"Creado: {nombre_archivo} ({len(parte)} registros)")

print("\nArchivos creados exitosamente!")
print("\nAhora ejecuta en 5 terminales diferentes:")
for i in range(NUM_PARTES):
    print(f"  Terminal {i+1}: python encriptar_cuentas_parte{i+1}.py")
