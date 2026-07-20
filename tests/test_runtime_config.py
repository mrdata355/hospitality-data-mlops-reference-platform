from __future__ import annotations

import importlib
from pathlib import Path

import hospitality_data_platform.config as config


def test_importing_runtime_config_does_not_write_to_disk(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("configuration import attempted to create a directory")

    monkeypatch.setattr(Path, "mkdir", fail_if_called)
    importlib.reload(config)


def test_runtime_directory_creation_is_explicit(tmp_path, monkeypatch):
    targets = (tmp_path / "raw", tmp_path / "models", tmp_path / "monitoring")
    monkeypatch.setattr(config, "RUNTIME_DIRECTORIES", targets)

    config.ensure_runtime_directories()

    assert all(path.is_dir() for path in targets)
