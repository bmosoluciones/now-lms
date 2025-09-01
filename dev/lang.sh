# Actualizar archivo de traducción
# Extraer nuevos textos
pybabel extract -F babel.cfg -o now_lms/translations/messages.pot .

# Actualizar archivos de idioma
pybabel update -i now_lms/translations/messages.pot -d now_lms/translations

# Luego edita los .po y recompila
pybabel compile -d now_lms/translations
