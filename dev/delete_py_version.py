import argparse
import os
import re
import shutil
import sys
import tempfile

SPECIAL_PREFIXES = ("-e", "git+", "http://", "https://", "file:", "ssh+", "-r", "--find-links", "--extra-index-url")

OPERATOR_PATTERNS = ["==", ">=", "<=", "~=", "!=", "===", ">", "<", "!="]


def is_special_line(s: str) -> bool:
    s_lower = s.lstrip().lower()
    return any(s_lower.startswith(p) for p in SPECIAL_PREFIXES)


def strip_version_from_spec(spec: str) -> str:
    # Remove any inline whitespace
    spec = spec.strip()
    # Find earliest operator occurrence
    idx = None
    for op in OPERATOR_PATTERNS:
        i = spec.find(op)
        if i != -1 and (idx is None or i < idx):
            idx = i
    if idx is not None:
        return spec[:idx].strip()
    # Also handle comma-separated multiple specs like "pkg>=1.0,<2.0"
    if "," in spec:
        return spec.split(",")[0].strip()
    return spec


def process_line(line: str) -> str:
    raw = line.rstrip("\n")
    stripped = raw.strip()
    if not stripped or stripped.startswith("#"):
        return raw  # blank or comment lines preserved

    if is_special_line(stripped):
        return raw  # preserve special entries as-is

    # Separate inline comment (a '#' preceded by whitespace)
    parts = re.split(r"\s+#", raw, maxsplit=1)
    left = parts[0].rstrip()
    comment = ("  #" + parts[1]) if len(parts) > 1 else ""

    # Separate environment marker (';') if present, preserve it
    left_parts = left.split(";", 1)
    spec_part = left_parts[0].strip()
    env_marker = (";" + left_parts[1].strip()) if len(left_parts) > 1 else ""

    name = strip_version_from_spec(spec_part)
    if not name:
        return raw  # fallback: preserve original if parsing failed

    return name + env_marker + comment


def main():
    parser = argparse.ArgumentParser(description="Quitar versiones de requirements.txt")
    parser.add_argument("file", nargs="?", default="requirements.txt", help="Ruta al requirements.txt")
    args = parser.parse_args()

    input_path = args.file
    if not os.path.exists(input_path):
        print(f"[ERROR] Archivo no encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    fd, tmp_path = tempfile.mkstemp(prefix="req_unfreeze_", text=True)
    os.close(fd)
    try:
        with open(input_path, "r", encoding="utf-8") as src, open(tmp_path, "w", encoding="utf-8") as dst:
            for line in src:
                dst.write(process_line(line) + "\n")
        shutil.move(tmp_path, input_path)
        print(f"Archivo '{input_path}' actualizado: versiones eliminadas.")
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


if __name__ == "__main__":
    main()
