def parse_po(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    entries = []
    current_msgid = []
    current_msgstr = []
    in_msgid = False
    in_msgstr = False
    is_fuzzy = False

    for i, line in enumerate(lines):
        line_strip = line.strip()
        if line_strip.startswith("#, fuzzy"):
            is_fuzzy = True
        elif line_strip.startswith("msgid"):
            in_msgid = True
            in_msgstr = False
            current_msgid = [line_strip[6:].strip('"')]
        elif line_strip.startswith("msgstr"):
            in_msgid = False
            in_msgstr = True
            current_msgstr = [line_strip[7:].strip('"')]
        elif line_strip.startswith('"') and in_msgid:
            current_msgid.append(line_strip.strip('"'))
        elif line_strip.startswith('"') and in_msgstr:
            current_msgstr.append(line_strip.strip('"'))
        elif line_strip == "" or i == len(lines) - 1:
            if current_msgid:
                msgid_str = "".join(current_msgid)
                msgstr_str = "".join(current_msgstr)
                if msgid_str != "":
                    entries.append({
                        "msgid": msgid_str,
                        "msgstr": msgstr_str,
                        "is_fuzzy": is_fuzzy
                    })
            is_fuzzy = False
            in_msgid = False
            in_msgstr = False
            current_msgid = []
            current_msgstr = []

    return entries

en_entries = parse_po("now_lms/translations/en/LC_MESSAGES/messages.po")
pt_entries = parse_po("now_lms/translations/pt_BR/LC_MESSAGES/messages.po")

en_incomplete = [e for e in en_entries if e["msgstr"] == "" or e["is_fuzzy"]]
pt_incomplete = [e for e in pt_entries if e["msgstr"] == "" or e["is_fuzzy"]]

print(f"EN Incomplete: {len(en_incomplete)}")
for e in en_incomplete:
    print(f"  ID: {repr(e['msgid'])} -> Current STR: {repr(e['msgstr'])} (fuzzy: {e['is_fuzzy']})")

print(f"\nPT_BR Incomplete: {len(pt_incomplete)}")
for e in pt_incomplete:
    print(f"  ID: {repr(e['msgid'])} -> Current STR: {repr(e['msgstr'])} (fuzzy: {e['is_fuzzy']})")
