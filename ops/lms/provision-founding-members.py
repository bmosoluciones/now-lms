#!/usr/bin/env python3
"""Provision founding-member student accounts on the production NOW-LMS.

This is the now-lms-owned copy of the estate provisioning tool (moved here from
intent-os 2026-07-29, owner order) with the post-rollout audit findings fixed:

* Inactive existing users are SKIPPED by default; touching them requires an
  explicit ``--allow-reactivate`` (the old behavior silently re-enabled
  offboarded users, reset their password, and could demote their role).
* Reactivation never demotes: ``tipo`` is only changed when the user is in
  ``--admins``; otherwise the existing role is preserved.
* Reactivation is reversible: the prior password hash and role are captured
  into the result CSV (``prior_hash_b64`` / ``prior_tipo``) and restored on
  rollback.
* Rollback also removes the enrollments/avance rows this tool created for
  already-active and reactivated users — not just fully-created users. The
  result CSV separates ``courses_enrolled`` (this run's writes, rollback-able)
  from ``courses_already`` (pre-existing, never touched).
* Old-format result CSVs (the 2026-07-28 live run) are still accepted by
  ``--rollback`` with the original created/reactivated-only semantics.

Runs from the dev box; all DB work executes inside the LMS app container over
SSH (``ssh <host> docker exec -i <container> python3 -``) so the app's own ORM,
argon2 hashing, and column defaults apply. Mirrors the admin-create route
(now_lms/vistas/users.py::crear_usuario), plus the bulk-enrollment caveat:
EstudianteCurso rows are accompanied by per-resource CursoRecursoAvance seed
rows owned by the *member* (the in-app helper would stamp the actor).

Modes
  dry-run (default)  report per-user planned action + collisions; zero writes
  --live             create users, enroll, seed avance rows
  --rollback FILE    delete exactly what a prior live run created (refuses any
                     user showing progress or a login)

Credentials are generated locally and travel only over the SSH stdin stream;
the container echoes back statuses, never passwords. The result CSV (which
includes plaintext passwords and prior hashes) lands mode 600 outside any
repo. Do not commit or mail it.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import secrets
import shlex
import subprocess
import sys
from pathlib import Path

DEFAULT_HOST = "intentsolutions"
DEFAULT_CONTAINER = "now-lms-app-1"
# The image ships no `python3` on PATH; the app runs on this interpreter.
CONTAINER_PYTHON = "/usr/bin/python3.12"
ACTOR = "intentadmin"  # audit-trail creado_por; must be an existing LMS user
MAX_USERS = 60  # sanity ceiling — this is a hand-vetted roster, never a bulk import

REMOTE_PY = r'''
import base64, json, sys

PAYLOAD = json.loads(sys.stdin.read())

from now_lms import lms_app
from now_lms.auth import proteger_passwd
from now_lms.db import (
    Curso,
    CursoRecurso,
    CursoRecursoAvance,
    CursoUsuarioAvance,
    EstudianteCurso,
    Usuario,
    database,
)

mode = PAYLOAD["mode"]
courses = PAYLOAD.get("courses", [])
actor = PAYLOAD["actor"]
admins = set(PAYLOAD.get("admins", []))
allow_reactivate = bool(PAYLOAD.get("allow_reactivate"))
out = {"mode": mode, "results": [], "errors": []}


def find_user(s, email):
    row = s.execute(database.select(Usuario).filter_by(usuario=email)).scalar_one_or_none()
    if row is None:
        row = s.execute(
            database.select(Usuario).filter_by(correo_electronico=email)
        ).scalar_one_or_none()
    return row


def remove_run_enrollments(s, username, codes):
    """Delete enrollments + seed avance rows this tool created (creado_por=actor)."""
    removed = []
    for code in codes:
        for row in s.execute(
            database.select(CursoRecursoAvance).filter_by(
                curso=code, usuario=username, creado_por=actor, completado=False
            )
        ).scalars():
            s.delete(row)
        enr = s.execute(
            database.select(EstudianteCurso).filter_by(curso=code, usuario=username)
        ).scalar_one_or_none()
        if enr is not None and enr.creado_por == actor:
            s.delete(enr)
            removed.append(code)
    return removed


with lms_app.app_context():
    s = database.session
    known = {
        c.codigo
        for c in s.execute(database.select(Curso)).scalars()
    }
    missing = [c for c in courses if c not in known]
    if missing:
        out["errors"].append("unknown course codes: %s" % ",".join(missing))
        print(json.dumps(out))
        sys.exit(2)

    resources = {}
    for code in courses:
        resources[code] = list(
            s.execute(database.select(CursoRecurso).filter_by(curso=code)).scalars()
        )

    if mode in ("dry-run", "live"):
        for u in PAYLOAD["users"]:
            email = u["email"]
            r = {"email": email, "action": None, "enrolled": [], "already": []}
            try:
                existing = find_user(s, email)
                if existing is not None and existing.activo:
                    r["action"] = "exists-active-skipped"
                elif existing is not None and not allow_reactivate:
                    # Safe default: never silently re-enable an offboarded user.
                    r["action"] = "exists-inactive-skipped"
                    out["results"].append(r)
                    continue
                elif existing is not None:
                    r["action"] = "reactivated" + ("-admin" if email in admins else "")
                    if mode == "live":
                        # Capture prior credential + role so rollback can restore them.
                        r["prior_hash_b64"] = base64.b64encode(
                            existing.acceso or b""
                        ).decode("ascii")
                        r["prior_tipo"] = existing.tipo
                        existing.activo = True
                        if email in admins:
                            existing.tipo = "admin"
                        existing.correo_electronico_verificado = True
                        existing.acceso = proteger_passwd(u["password"])
                        existing.modificado_por = actor
                else:
                    r["action"] = "created" + ("-admin" if email in admins else "")
                    if mode == "live":
                        existing = Usuario(
                            usuario=email,
                            acceso=proteger_passwd(u["password"]),
                            nombre=u["nombre"],
                            apellido=u["apellido"],
                            correo_electronico=email,
                            tipo="admin" if email in admins else "student",
                            activo=True,
                            visible=True,
                            correo_electronico_verificado=True,
                            creado_por=actor,
                        )
                        s.add(existing)

                username = existing.usuario if existing is not None else email
                for code in courses:
                    enrolled = s.execute(
                        database.select(EstudianteCurso).filter_by(
                            curso=code, usuario=username
                        )
                    ).scalar_one_or_none()
                    if enrolled is not None:
                        r["already"].append(code)
                        continue
                    r["enrolled"].append(code)
                    if mode == "live":
                        s.add(
                            EstudianteCurso(
                                curso=code, usuario=username, vigente=True, creado_por=actor
                            )
                        )
                        for res in resources[code]:
                            have = s.execute(
                                database.select(CursoRecursoAvance).filter_by(
                                    curso=code, recurso=res.id, usuario=username
                                )
                            ).scalar_one_or_none()
                            if have is None:
                                s.add(
                                    CursoRecursoAvance(
                                        curso=code,
                                        recurso=res.id,
                                        usuario=username,
                                        completado=False,
                                        requerido=res.requerido,
                                        creado_por=actor,
                                    )
                                )
                if mode == "live":
                    s.commit()
            except Exception as exc:  # noqa: BLE001 — per-user isolation, run continues
                s.rollback()
                r["action"] = "error"
                r["error"] = str(exc)[:300]
            out["results"].append(r)

    elif mode == "rollback":
        for u in PAYLOAD["users"]:
            email = u["email"]
            status = u.get("status") or ""
            run_courses = u.get("courses_enrolled") or []
            r = {"email": email, "action": None}
            try:
                existing = find_user(s, email)
                if existing is None:
                    r["action"] = "absent"
                    out["results"].append(r)
                    continue
                username = existing.usuario
                progressed = s.execute(
                    database.select(CursoRecursoAvance).filter_by(
                        usuario=username, completado=True
                    )
                ).first()
                if existing.ultimo_acceso is not None or progressed is not None:
                    r["action"] = "refused-has-activity"
                    out["results"].append(r)
                    continue
                if status.startswith("created"):
                    for model in (CursoRecursoAvance, CursoUsuarioAvance, EstudianteCurso):
                        for row in s.execute(
                            database.select(model).filter_by(usuario=username)
                        ).scalars():
                            s.delete(row)
                    s.delete(existing)
                    r["action"] = "deleted"
                elif status.startswith("reactivated"):
                    removed = remove_run_enrollments(s, username, run_courses)
                    prior_hash = u.get("prior_hash_b64") or ""
                    if prior_hash:
                        existing.acceso = base64.b64decode(prior_hash)
                    prior_tipo = u.get("prior_tipo") or ""
                    if prior_tipo:
                        existing.tipo = prior_tipo
                    existing.activo = False
                    existing.modificado_por = actor
                    r["action"] = "re-deactivated" + (
                        "-restored" if prior_hash else ""
                    )
                    r["unenrolled"] = removed
                elif status.startswith("exists-active-skipped") and run_courses:
                    removed = remove_run_enrollments(s, username, run_courses)
                    r["action"] = "unenrolled"
                    r["unenrolled"] = removed
                else:
                    r["action"] = "skipped-status-%s" % status
                s.commit()
            except Exception as exc:  # noqa: BLE001
                s.rollback()
                r["action"] = "error"
                r["error"] = str(exc)[:300]
            out["results"].append(r)

print(json.dumps(out))
'''


def read_roster(path: Path) -> list[dict]:
    users = []
    seen = set()
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            email = (row.get("email") or "").strip().lower()
            if not email:
                continue
            if email in seen:
                sys.exit(f"duplicate roster email: {email}")
            seen.add(email)
            users.append(
                {
                    "email": email,
                    "nombre": (row.get("first_name") or "").strip(),
                    "apellido": (row.get("last_name") or "").strip(),
                }
            )
    if not users:
        sys.exit("roster is empty")
    if len(users) > MAX_USERS:
        sys.exit(f"roster has {len(users)} users — over the {MAX_USERS} sanity ceiling")
    return users


def read_result(path: Path) -> list[dict]:
    """Load a result CSV for rollback. Accepts both formats:

    new (this script): email,username,password,courses_enrolled,courses_already,
                       status,prior_hash_b64,prior_tipo
    old (2026-07-28):  email,username,password,courses,status — only
                       created*/reactivated* rows are rollback-able, and
                       reactivated users are re-deactivated without hash
                       restore (the old run never captured it).
    """
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames or []
        new_format = "courses_enrolled" in fields
        rows = []
        for r in reader:
            status = (r.get("status") or "")
            if new_format:
                enrolled = [c for c in (r.get("courses_enrolled") or "").split(";") if c]
                if not (status.startswith(("created", "reactivated")) or enrolled):
                    continue
                rows.append(
                    {
                        "email": r["email"],
                        "status": status,
                        "courses_enrolled": enrolled,
                        "prior_hash_b64": r.get("prior_hash_b64") or "",
                        "prior_tipo": r.get("prior_tipo") or "",
                    }
                )
            else:
                if not status.startswith(("created", "reactivated")):
                    continue
                rows.append({"email": r["email"], "status": status, "courses_enrolled": []})
    if not rows:
        sys.exit("result CSV has no rollback-able rows")
    return rows


def run_remote_stdin(host: str, container: str, payload: dict) -> dict:
    """Stream the remote program + payload over one SSH stdin pipe."""
    program = REMOTE_PY
    data = json.dumps(payload)
    # python3 -c reads the program from argv; payload arrives on stdin so
    # credentials never appear in argv or process listings. ssh joins argv into
    # one remote shell string, so the program must be shell-quoted.
    remote_cmd = f"docker exec -i {container} {CONTAINER_PYTHON} -c {shlex.quote(program)}"
    proc = subprocess.run(
        ["ssh", host, remote_cmd],
        input=data,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode not in (0, 2):
        sys.exit(f"remote run failed rc={proc.returncode}\n{proc.stderr[-2000:]}")
    line = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        sys.exit(f"unparseable remote output:\n{proc.stdout[-2000:]}\n{proc.stderr[-1000:]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--roster", type=Path, help="CSV with email,first_name,last_name")
    ap.add_argument("--courses", default="", help="comma-separated course codes")
    ap.add_argument(
        "--admins", default="",
        help="comma-separated emails created as tipo=admin (or upgraded on reactivate)",
    )
    ap.add_argument(
        "--allow-reactivate", action="store_true",
        help="permit re-enabling inactive existing users (password reset + reactivation); "
        "without this flag they are skipped",
    )
    ap.add_argument("--live", action="store_true", help="perform writes (default dry-run)")
    ap.add_argument("--rollback", type=Path, help="result CSV from a prior live run")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if args.rollback:
        payload = {
            "mode": "rollback",
            "actor": ACTOR,
            "users": read_result(args.rollback),
        }
        result = run_remote_stdin(args.host, args.container, payload)
        for r in result["results"]:
            extra = f" unenrolled={','.join(r['unenrolled'])}" if r.get("unenrolled") else ""
            err = f" ({r.get('error')})" if r.get("error") else ""
            print(f"{r['email']}: {r['action']}{extra}{err}")
        bad = [r for r in result["results"] if r["action"] in ("error", "refused-has-activity")]
        sys.exit(1 if bad else 0)

    if not args.roster:
        ap.error("--roster is required (or use --rollback)")
    courses = [c.strip() for c in args.courses.split(",") if c.strip()]
    if not courses:
        ap.error("--courses is required for dry-run/live")

    users = read_roster(args.roster)
    passwords = {}
    if args.live:
        for u in users:
            passwords[u["email"]] = secrets.token_urlsafe(12)
            u["password"] = passwords[u["email"]]

    admins = [a.strip().lower() for a in args.admins.split(",") if a.strip()]
    unknown_admins = [a for a in admins if a not in {u["email"] for u in users}]
    if unknown_admins:
        sys.exit(f"--admins not on roster: {','.join(unknown_admins)}")
    payload = {
        "mode": "live" if args.live else "dry-run",
        "actor": ACTOR,
        "courses": courses,
        "admins": admins,
        "allow_reactivate": args.allow_reactivate,
        "users": users,
    }
    result = run_remote_stdin(args.host, args.container, payload)
    if result.get("errors"):
        for e in result["errors"]:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    counts: dict[str, int] = {}
    for r in result["results"]:
        counts[r["action"]] = counts.get(r["action"], 0) + 1
        flags = ""
        if r.get("already"):
            flags = " already-enrolled:" + ",".join(r["already"])
        if r.get("error"):
            flags += f" ({r['error']})"
        print(f"{r['email']}: {r['action']} enroll={','.join(r['enrolled']) or '-'}{flags}")
    print(f"\nsummary: {json.dumps(counts)} courses={','.join(courses)} mode={payload['mode']}")

    if args.live:
        out = args.out or Path.home() / "Downloads" / (
            "lms-founding-result-%s.csv" % datetime.date.today().isoformat()
        )
        out.touch(mode=0o600, exist_ok=True)
        out.chmod(0o600)
        with out.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(
                [
                    "email", "username", "password", "courses_enrolled",
                    "courses_already", "status", "prior_hash_b64", "prior_tipo",
                ]
            )
            for r in result["results"]:
                pw = passwords.get(r["email"], "") if r["action"].startswith(("created", "reactivated")) else ""
                w.writerow(
                    [
                        r["email"], r["email"], pw,
                        ";".join(r["enrolled"]), ";".join(r.get("already", [])),
                        r["action"], r.get("prior_hash_b64", ""), r.get("prior_tipo", ""),
                    ]
                )
        print(f"result CSV (mode 600, passwords + prior hashes inside): {out}")
        errors = [r for r in result["results"] if r["action"] == "error"]
        sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
