@echo off
echo Dividiendo archivo en 10 partes...
python dividir_archivo.py

echo.
echo Ejecutando encriptacion en 10 terminales...
start cmd /k "python encriptar_parte.py 1"
start cmd /k "python encriptar_parte.py 2"
start cmd /k "python encriptar_parte.py 3"
start cmd /k "python encriptar_parte.py 4"
start cmd /k "python encriptar_parte.py 5"
start cmd /k "python encriptar_parte.py 6"
start cmd /k "python encriptar_parte.py 7"
start cmd /k "python encriptar_parte.py 8"
start cmd /k "python encriptar_parte.py 9"
start cmd /k "python encriptar_parte.py 10"

echo.
echo 10 terminales abiertas procesando en paralelo!
pause
