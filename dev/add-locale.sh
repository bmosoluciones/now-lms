#!/bin/bash
# Add (or refresh) a translation catalog for a locale.
#
# Usage:
#   dev/add-locale.sh <locale>     # e.g. dev/add-locale.sh fr
#
# Runs the clean Babel workflow end to end:
#   1. extract the message template from Python + Jinja sources
#   2. init the locale catalog (or update it if it already exists)
#   3. compile the catalog to messages.mo
#
# After running, edit now_lms/translations/<locale>/LC_MESSAGES/messages.po,
# re-run `pybabel compile -d now_lms/translations -l <locale>`, and add the
# locale to ConfigForm.lang choices in now_lms/forms/__init__.py.
# See docs/development/i18n-add-a-language.md for the full guide.
set -euo pipefail

LOCALE="${1:-}"
if [ -z "$LOCALE" ]; then
    echo "Usage: dev/add-locale.sh <locale>   (e.g. fr, de, it, fr_CA)" >&2
    exit 1
fi

TRANSLATIONS_DIR="now_lms/translations"
POT="${TRANSLATIONS_DIR}/messages.pot"
CATALOG="${TRANSLATIONS_DIR}/${LOCALE}/LC_MESSAGES/messages.po"

echo "1/3 Extracting message template -> ${POT}"
pybabel extract -F babel.cfg -o "${POT}" .

if [ -f "${CATALOG}" ]; then
    echo "2/3 Catalog exists, updating -> ${CATALOG}"
    pybabel update -i "${POT}" -d "${TRANSLATIONS_DIR}" -l "${LOCALE}"
else
    echo "2/3 Initializing new catalog -> ${CATALOG}"
    pybabel init -i "${POT}" -d "${TRANSLATIONS_DIR}" -l "${LOCALE}"
fi

echo "3/3 Compiling catalog -> ${LOCALE}/LC_MESSAGES/messages.mo"
pybabel compile -d "${TRANSLATIONS_DIR}" -l "${LOCALE}"

echo
echo "Done. Now edit ${CATALOG}, fill in each msgstr (preserve every"
echo "placeholder/HTML tag exactly), then run:"
echo "    pybabel compile -d ${TRANSLATIONS_DIR} -l ${LOCALE}"
echo "and add (\"${LOCALE}\", \"<Name>\") to ConfigForm.lang choices in now_lms/forms/__init__.py."
