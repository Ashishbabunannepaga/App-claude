"""Loads config.yaml and fills in defaults."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Category:
    name: str
    keywords: list[str]
    requires: list[str] = field(default_factory=list)
    ignore: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class Named:
    name: str
    match: list[str]


@dataclass
class Config:
    work_dir: Path
    store_dir: Path
    output_dir: Path
    include_stores: list[str]
    skip_folders: list[str]
    min_image_kb: int
    skip_extensions: list[str]
    organize_mode: str
    layout: str
    filename: str
    own_domains: list[str]
    free_mail_domains: list[str]
    categories: list[Category]
    fallback_category: str
    insurers: list[Named]
    clients: list[Named]
    ai_enabled: bool
    ai_provider: str
    ai_key_file: Path | None
    ai_model: str
    ai_max_chars: int
    ai_workers: int
    source_path: Path | None = None

    @property
    def db_path(self) -> Path:
        return self.work_dir / "mailsorter.db"

    @property
    def category_names(self) -> list[str]:
        return [c.name for c in self.categories] + [self.fallback_category]


def _lower_list(values) -> list[str]:
    return [str(v).strip().lower() for v in (values or []) if str(v).strip()]


def _named(items) -> list[Named]:
    out = []
    for it in items or []:
        name = str(it["name"]).strip()
        out.append(Named(name=name, match=_lower_list(it.get("match")) or [name.lower()]))
    return out


def load_config(path: str | os.PathLike) -> Config:
    path = Path(path)
    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    paths = raw.get("paths", {})
    work_dir = Path(os.path.expandvars(paths.get("work_dir", "work")))
    if not work_dir.is_absolute():
        work_dir = (path.parent / work_dir).resolve()
    store_dir = Path(os.path.expandvars(paths.get("store_dir") or str(work_dir / "store")))
    if not store_dir.is_absolute():
        store_dir = (path.parent / store_dir).resolve()
    output_dir = Path(os.path.expandvars(paths.get("output_dir", "output")))
    if not output_dir.is_absolute():
        output_dir = (path.parent / output_dir).resolve()

    ol = raw.get("outlook", {})
    org = raw.get("organize", {})
    ai = raw.get("ai", {})

    cats = []
    for c in raw.get("categories", []):
        cats.append(Category(
            name=str(c["name"]).strip(),
            keywords=_lower_list(c.get("keywords")),
            requires=_lower_list(c.get("requires")),
            ignore=_lower_list(c.get("ignore")),
            description=str(c.get("description", "")).strip(),
        ))
    if not cats:
        raise ValueError("config.yaml has no categories")

    provider = str(ai.get("provider", "openai")).strip().lower()
    if provider not in ("openai", "anthropic"):
        raise ValueError("ai.provider must be 'openai' or 'anthropic'")
    key_file = str(ai.get("api_key_file", "api-key.txt")).strip()
    key_path = Path(os.path.expandvars(key_file)) if key_file else None
    if key_path and not key_path.is_absolute():
        key_path = (path.parent / key_path).resolve()
    default_model = "gpt-4o-mini" if provider == "openai" else "claude-opus-5-5"

    mode = str(org.get("mode", "move")).lower()
    if mode not in ("move", "copy"):
        raise ValueError("organize.mode must be 'move' or 'copy'")

    return Config(
        work_dir=work_dir,
        store_dir=store_dir,
        output_dir=output_dir,
        include_stores=[str(s) for s in ol.get("include_stores") or []],
        skip_folders=_lower_list(ol.get("skip_folders")),
        min_image_kb=int(ol.get("min_image_kb", 40)),
        skip_extensions=_lower_list(ol.get("skip_extensions")),
        organize_mode=mode,
        layout=str(org.get("layout", "{category}/{fy}/{client}")),
        filename=str(org.get("filename", "{date}_{insurer}_{name}")),
        own_domains=_lower_list(raw.get("own_domains")),
        free_mail_domains=_lower_list(raw.get("free_mail_domains")),
        categories=cats,
        fallback_category=str(raw.get("fallback_category", "Other - Needs Review")),
        insurers=_named(raw.get("insurers")),
        clients=_named(raw.get("clients")),
        ai_enabled=bool(ai.get("enabled", False)),
        ai_provider=provider,
        ai_key_file=key_path,
        ai_model=str(ai.get("model") or default_model),
        ai_max_chars=int(ai.get("max_chars", 2500)),
        ai_workers=max(1, int(ai.get("workers", 4))),
        source_path=path,
    )
