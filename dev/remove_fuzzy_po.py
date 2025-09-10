import sys
import re


def limpiar_fuzzy_po(ruta_po):
    with open(ruta_po, encoding="utf-8") as f:
        lineas = f.readlines()

    nuevas_lineas = []
    i = 0
    while i < len(lineas):
        if lineas[i].startswith("#, fuzzy"):
            # Saltar el comentario
            i += 1
            # Procesar el bloque msgid/msgstr
            bloque = []
            while i < len(lineas) and not lineas[i].strip().startswith("#, fuzzy"):
                bloque.append(lineas[i])
                if lineas[i].startswith("msgstr"):
                    # Reemplaza la traducción por vacío
                    nuevas_lineas.append(re.sub(r'msgstr\s+".*"', 'msgstr ""', lineas[i]))
                    i += 1
                    break
                else:
                    nuevas_lineas.append(lineas[i])
                i += 1
            # El resto del bloque ya se procesó
        else:
            nuevas_lineas.append(lineas[i])
            i += 1

    with open(ruta_po, "w", encoding="utf-8") as f:
        f.writelines(nuevas_lineas)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python remove_fuzzy_po.py <archivo.po>")
        sys.exit(1)
    limpiar_fuzzy_po(sys.argv[1])
