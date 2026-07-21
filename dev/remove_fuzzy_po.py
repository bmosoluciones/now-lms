import os
import sys
import re


def validate_po_path(ruta_po: str) -> str:
    resolved = os.path.realpath(ruta_po)
    if not resolved.startswith(os.path.realpath(".")):
        raise ValueError(f"Path must be within current directory: {ruta_po}")
    if not os.path.isfile(resolved):
        raise FileNotFoundError(f"File not found: {ruta_po}")
    return resolved


def limpiar_fuzzy_po(ruta_po):
    po_path = validate_po_path(ruta_po)
    with open(po_path, encoding="utf-8") as f:
        lineas = f.readlines()

    nuevas_lineas = []
    i = 0
    while i < len(lineas):
        if lineas[i].startswith("#, fuzzy"):
            i += 1
            while i < len(lineas) and not lineas[i].strip().startswith("#, fuzzy"):
                if lineas[i].startswith("msgstr"):
                    nuevas_lineas.append(re.sub(r'msgstr\s+".*"', 'msgstr ""', lineas[i]))
                    i += 1
                    break
                else:
                    nuevas_lineas.append(lineas[i])
                i += 1
        else:
            nuevas_lineas.append(lineas[i])
            i += 1

    with open(po_path, "w", encoding="utf-8") as f:
        f.writelines(nuevas_lineas)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python remove_fuzzy_po.py <archivo.po>")
        sys.exit(1)
    try:
        limpiar_fuzzy_po(sys.argv[1])
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
