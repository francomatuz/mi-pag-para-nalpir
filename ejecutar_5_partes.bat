@echo off
echo Dividiendo archivo en 5 partes...
python dividir_archivo.py

echo.
echo Ejecutando encriptacion en 5 terminales...
start cmd /k "python encriptar_parte.py 1"
start cmd /k "python encriptar_parte.py 2"
start cmd /k "python encriptar_parte.py 3"
start cmd /k "python encriptar_parte.py 4"
start cmd /k "python encriptar_parte.py 5"

echo.
echo 5 terminales abiertas procesando en paralelo!
pause
