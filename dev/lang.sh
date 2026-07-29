# Actualizar archivo de traducción
# Extraer nuevos textos
#
# -k _l es obligatorio: `_l` (lazy_gettext) no está en las palabras clave por
# defecto de Babel, así que sin esta opción las etiquetas de formulario escritas
# con _l() no se extraen y quedan imposibles de traducir.
pybabel extract -F babel.cfg -k _l -o now_lms/translations/messages.pot .

# Actualizar archivos de idioma
pybabel update -i now_lms/translations/messages.pot -d now_lms/translations

# Luego edita los .po y recompila
pybabel compile -d now_lms/translations
