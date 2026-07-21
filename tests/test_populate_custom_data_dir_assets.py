# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Regression test for bundled frontend asset population with a custom data dir.

With a custom NOW_LMS_DATA_DIR, Flask's static_folder points at that
directory, so bundled frontend assets (node_modules — Bootstrap etc.) must be
copied there or every static asset 404s and the UI renders unstyled.

populate_custmon_data_dir() previously populated only when the data dir was
missing or completely empty. That check never actually fires in the real
boot sequence: initial_setup() writes default-course files into the data dir
*before* this function runs, so by the time it's checked the directory is
already non-empty — node_modules is never copied. The fix adds an explicit
"node_modules is absent" check so a non-empty-but-unstyled data dir still
gets populated, without disturbing files already there
(copytree(dirs_exist_ok=True) merges).
"""

import importlib

from now_lms.db import initial_data

# now_lms/__init__.py defines its own module-level `config()` CLI function,
# which shadows the `now_lms.config` submodule as a package attribute once
# now_lms is imported — `import now_lms.config as config_module` would bind
# to that function, not the submodule. importlib.import_module() always
# resolves the real submodule regardless of that attribute shadowing.
config_module = importlib.import_module("now_lms.config")


def test_populates_bundled_assets_when_data_dir_is_nonempty_but_node_modules_is_missing(tmp_path, monkeypatch):
    """The exact bug scenario: a custom data dir that already has files in it
    (e.g. from initial_setup()'s default-course population) but never got the
    bundled node_modules copied in."""
    bundled_base = tmp_path / "bundled_base"
    bundled_base.mkdir()
    (bundled_base / "node_modules" / "bootstrap" / "dist").mkdir(parents=True)
    (bundled_base / "node_modules" / "bootstrap" / "dist" / "bootstrap.min.css").write_text("/* bundled css */")

    custom_data_dir = tmp_path / "custom_data"
    custom_data_dir.mkdir()
    (custom_data_dir / "examples").mkdir()
    (custom_data_dir / "examples" / "already_uploaded.txt").write_text("pre-existing upload")

    monkeypatch.setattr(initial_data, "DIRECTORIO_ARCHIVOS", str(custom_data_dir))
    monkeypatch.setattr(config_module, "DIRECTORIO_ARCHIVOS_BASE", str(bundled_base))

    initial_data.populate_custmon_data_dir()

    copied_css = custom_data_dir / "node_modules" / "bootstrap" / "dist" / "bootstrap.min.css"
    assert copied_css.exists(), "bundled node_modules assets must be copied even when the data dir is already non-empty"
    assert copied_css.read_text() == "/* bundled css */"
    # Existing uploads must survive the merge — this is not a destructive copy.
    assert (custom_data_dir / "examples" / "already_uploaded.txt").read_text() == "pre-existing upload"


def test_does_not_touch_data_dir_when_it_matches_the_bundled_base(tmp_path, monkeypatch):
    """Sanity control: when DIRECTORIO_ARCHIVOS == DIRECTORIO_ARCHIVOS_BASE
    (no custom data dir configured), the function must be a no-op — proves
    the previous test is exercising the "custom dir" branch, not a
    default-path coincidence."""
    same_dir = tmp_path / "same"
    same_dir.mkdir()

    monkeypatch.setattr(initial_data, "DIRECTORIO_ARCHIVOS", str(same_dir))
    monkeypatch.setattr(config_module, "DIRECTORIO_ARCHIVOS_BASE", str(same_dir))

    initial_data.populate_custmon_data_dir()

    assert list(same_dir.iterdir()) == []
