# Update the translation catalogues.
#
# -k _l is load-bearing. `_l` (lazy_gettext) is NOT one of Babel's default
# keywords, so without it every _l() string in the codebase is invisible to the
# extractor: no msgid is written, and no translator can reach the string. That is
# an extraction gap, not a translation gap, and it hides itself — the catalogue
# looks complete because the missing strings were never offered to it.
#
# Measured on this tree with Babel 2.18: 2774 msgids without the flag, 2839 with
# it. The 65 strings it recovers include every option in the profile Gender and
# Qualification dropdowns, which is why those rendered in Spanish under an
# English label. If you change this line, check that the msgid count moves.
#
# -k _n:1,2 declares the project's ngettext alias the same way: singular and
# plural argument positions for _n(), so the documented plural helper extracts.

# Extract translatable strings
pybabel extract -F babel.cfg -k _l -k _n:1,2 -o now_lms/translations/messages.pot .

# Merge into the per-language catalogues
pybabel update -i now_lms/translations/messages.pot -d now_lms/translations

# Then edit the .po files and recompile
pybabel compile -d now_lms/translations

# Verify the gate passes (refuse stale catalogs before they ship).
# Skip the check if a virtualenv Python isn't on PATH (gate requires Babel + flask_babel).
if [ -x .venv/bin/python ]; then
    PYTHON=./.venv/bin/python bash dev/catalog_freshness_check.sh
fi
