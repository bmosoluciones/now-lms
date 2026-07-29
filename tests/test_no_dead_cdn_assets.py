# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Bundled themes must not load third-party assets they never use.

Every theme pulled ionicons from unpkg.com on every page render — two extra
third-party requests per page — while no template contained a single
``<ion-icon>`` element. This test keeps that from creeping back, and keeps the
pairing honest: if a theme ever does start using ion-icon, the loader is
allowed again.
"""

from __future__ import annotations

from pathlib import Path

THEMES_DIR = Path(__file__).resolve().parent.parent / "now_lms" / "templates" / "themes"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "now_lms" / "templates"


def _all_template_text() -> str:
    return "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in TEMPLATES_DIR.rglob("*")
        if p.suffix in {".j2", ".html"}
    )


def test_ionicons_is_not_loaded_unless_it_is_used():
    """No ionicons loader while no template renders an <ion-icon>."""
    templates = _all_template_text()
    uses_element = "<ion-icon" in templates
    loads_library = "ionicons" in templates

    if uses_element:  # pragma: no cover - only if a theme adopts ion-icon later
        assert loads_library, "a template uses <ion-icon> but no theme loads the library"
    else:
        assert not loads_library, (
            "themes load the ionicons library from a CDN but no template uses <ion-icon>; "
            "drop the loader or use the element"
        )


def test_the_theme_tree_was_actually_scanned():
    """Guard the scanner — an empty read would make the check above vacuous."""
    text = _all_template_text()
    assert len(text) > 100_000
    assert THEMES_DIR.is_dir()
