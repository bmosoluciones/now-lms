# Actualizar archivo de traducción
# Extraer nuevos textos
#
# Los alias propios del proyecto no están en las palabras clave por defecto de
# Babel, así que hay que declararlos o sus textos no se extraen y quedan
# imposibles de traducir:
#   -k _l        -> _l() / lazy_gettext, las etiquetas de formulario
#   -k _n:1,2    -> _n() / ngettext, singular y plural
pybabel extract -F babel.cfg -k _l -k _n:1,2 -o now_lms/translations/messages.pot .

# Actualizar archivos de idioma
pybabel update -i now_lms/translations/messages.pot -d now_lms/translations

# Recompilar
pybabel compile -d now_lms/translations

# Verify the gate passes (refuse stale catalogs before they ship).
# Skip the check if a virtualenv Python isn't on PATH (gate requires Babel + flask_babel).
if [ -x .venv/bin/python ]; then
    PYTHON=./.venv/bin/python bash dev/catalog_freshness_check.sh
fi
