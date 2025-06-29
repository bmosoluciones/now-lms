import subprocess
import os
import shutil

# Archivos de entrada y salida
input_file = "requirements.txt"
temp_file = "requirements_with_versions.txt"

# Leer los paquetes
with open(input_file, "r") as f:
    packages = [line.strip() for line in f if line.strip()]

output_lines = []

# Procesar cada paquete
for package in packages:
    try:
        # Ejecutar 'pip show' para obtener la versión
        result = subprocess.run(["pip", "show", package], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            # Buscar la línea de la versión
            for line in result.stdout.splitlines():
                if line.startswith("Version:"):
                    version = line.split(":", 1)[1].strip()
                    output_lines.append(f"{package}=={version}")
                    break
        else:
            print(f"[ADVERTENCIA] El paquete '{package}' no está instalado.")
            output_lines.append(package)  # Lo escribe sin versión

    except Exception as e:
        print(f"[ERROR] No se pudo procesar '{package}': {e}")
        output_lines.append(package)

# Guardar el archivo temporal con versiones
with open(temp_file, "w") as f:
    f.write("\n".join(output_lines))

# Reemplazar el archivo original y eliminar el temporal
shutil.move(temp_file, input_file)

print(f"\nArchivo '{input_file}' actualizado correctamente con las versiones.")
