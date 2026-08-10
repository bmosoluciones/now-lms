#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Export every Community Hub post, reply and moderation event to JSON.

This is the Hub's rollback path, and under ADR-10 it carries more weight than it
would have under ADR-8. ADR-8 kept post bodies in the native ``foro_mensaje``, so
unregistering the blueprint left member content sitting in a platform table.
ADR-10 gave the Hub its own tables, which removed a silent data-loss path but
means member prose now lives ONLY here. So: export before any destructive
operation, and never drop these tables on production without a fresh export in
hand.

Deliberately includes:

* Every post and reply, hidden ones too. A moderator hiding something is not a
  reason to lose it, and nothing in the Hub hard-deletes.
* The full moderation trail, so the record of who did what survives the data.

Deliberately excludes the liker list. Aggregate like counts are public in the
product and the individual list is private; an export is not a licence to
compile something the application refuses to show.

Usage::

    DATABASE_URL=... python3 scripts/export_community.py > community-backup.json
    DATABASE_URL=... python3 scripts/export_community.py --out backup.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime

from now_lms import app, database
from now_lms.db import (
    ComunidadEventoModeracion,
    ComunidadPublicacion,
    ComunidadReaccion,
    Usuario,
    utc_now,
)


def _iso(valor):
    """Dates and datetimes to ISO strings; everything else unchanged."""
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    return valor


def _nombres() -> dict[str, str]:
    """Username to display name, so an export is readable without the user table."""
    filas = database.session.execute(database.select(Usuario)).scalars().all()
    return {u.usuario: " ".join(p for p in (u.nombre, u.apellido) if p) or u.usuario for u in filas}


def exportar() -> dict:
    """Build the export payload."""
    nombres = _nombres()

    conteos = dict(
        database.session.execute(
            database.select(ComunidadReaccion.publicacion_id, database.func.count(ComunidadReaccion.id)).group_by(
                ComunidadReaccion.publicacion_id
            )
        ).all()
    )

    eventos: dict[str, list] = {}
    for evento in database.session.execute(
        database.select(ComunidadEventoModeracion).order_by(ComunidadEventoModeracion.ocurrido_en)
    ).scalars():
        eventos.setdefault(evento.publicacion_id, []).append(
            {
                "tipo": evento.tipo,
                "actor": evento.actor,
                "motivo": evento.motivo,
                "ocurrido_en": _iso(evento.ocurrido_en),
            }
        )

    todas = database.session.execute(
        database.select(ComunidadPublicacion).order_by(ComunidadPublicacion.fecha_creacion)
    ).scalars().all()

    respuestas: dict[str, list] = {}
    raices = []
    for fila in todas:
        registro = {
            "id": fila.id,
            "autor": fila.usuario,
            "autor_nombre": nombres.get(fila.usuario, fila.usuario),
            "contenido": fila.contenido,
            "fecha_creacion": _iso(fila.fecha_creacion),
            "estado_moderacion": fila.estado_moderacion,
        }
        if fila.parent_id is None:
            registro.update(
                {
                    "titulo": fila.titulo,
                    "tipo": fila.tipo,
                    "enlace_build": fila.enlace_build,
                    "fijado": bool(fila.fijado),
                    "estado": fila.estado,
                    # Aggregate only. The liker list stays private, as it is in the product.
                    "likes": conteos.get(fila.id, 0),
                    "moderacion": eventos.get(fila.id, []),
                    "respuestas": [],
                }
            )
            raices.append(registro)
        else:
            respuestas.setdefault(fila.parent_id, []).append(registro)

    for raiz in raices:
        raiz["respuestas"] = respuestas.get(raiz["id"], [])

    huerfanas = sum(len(v) for k, v in respuestas.items() if k not in {r["id"] for r in raices})

    return {
        "exportado_en": utc_now().replace(tzinfo=None).isoformat(),
        "adr": "ADR-10 (000-docs/017-AT-ADEC)",
        "totales": {
            "publicaciones": len(raices),
            "respuestas": sum(len(r["respuestas"]) for r in raices),
            "reacciones": sum(conteos.values()),
            "eventos_moderacion": sum(len(v) for v in eventos.values()),
            # Should always be 0: parent_id cascades. Non-zero means something is wrong.
            "respuestas_huerfanas": huerfanas,
        },
        "publicaciones": raices,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the Community Hub to JSON.")
    parser.add_argument("--out", help="write here instead of stdout")
    args = parser.parse_args()

    with app.app_context():
        payload = exportar()

    texto = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(texto)
        totales = payload["totales"]
        print(
            f"Wrote {args.out}: {totales['publicaciones']} posts, {totales['respuestas']} replies, "
            f"{totales['reacciones']} likes, {totales['eventos_moderacion']} moderation events.",
            file=sys.stderr,
        )
    else:
        print(texto)


if __name__ == "__main__":
    main()
