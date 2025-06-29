import pkg_resources

# Archivo de entrada y salida
input_file = "requirements.txt"
output_file = "requirements_with_versions.txt"

# Leer los paquetes
with open(input_file, "r") as f:
    packages = [line.strip() for line in f if line.strip()]

output_lines = []

# Procesar cada paquete
for package in packages:
    try:
        # Obtener la versión instalada
        version = pkg_resources.get_distribution(package).version
        output_lines.append(f"{package}=={version}")
    except pkg_resources.DistributionNotFound:
        print(f"[ADVERTENCIA] El paquete '{package}' no está instalado en el entorno actual.")
        output_lines.append(package)  # Lo escribe sin versión

# Guardar el nuevo archivo con versiones
with open(output_file, "w") as f:
    f.write("\n".join(output_lines))

print(f"\nArchivo '{output_file}' generado correctamente.")
