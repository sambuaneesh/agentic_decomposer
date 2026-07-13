"""Walks a monolith codebase and collects basic facts about Java sources.

The walker is intentionally lightweight: no parsing of statements or
expressions. It uses regular expressions to find ``package``, ``class``,
``interface``, ``enum``, and annotation declarations. This is sufficient for
the framework's needs (component grouping by package, stereotype detection by
class name, and serving Java text to the LLM-based views).

For full AST-level parsing the deterministic views use ``javalang`` on top of
this walker's :class:`SourceFile` records.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator


_PACKAGE_RE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.MULTILINE)
_TYPE_RE = re.compile(
    r"^\s*(?:public\s+|private\s+|protected\s+|abstract\s+|final\s+|static\s+)*"
    r"(class|interface|enum|@interface)\s+(\w+)",
    re.MULTILINE,
)


@dataclass(frozen=True)
class SourceFile:
    """One ``.java`` source file with lightweight metadata."""

    path: Path
    package: str
    types: tuple[tuple[str, str], ...]   # ((kind, simple_name), ...)
    text: str

    @property
    def primary_type(self) -> tuple[str, str] | None:
        """First declared type in the file, or ``None`` if none was found."""
        return self.types[0] if self.types else None

    @property
    def primary_fqn(self) -> str | None:
        ty = self.primary_type
        if ty is None:
            return None
        return f"{self.package}.{ty[1]}" if self.package else ty[1]


@dataclass
class SourceWalker:
    """Walk a codebase and yield :class:`SourceFile` records lazily.

    Parameters
    ----------
    root:
        Path to the codebase folder (one of ``codebases/<system>``).
    excluded_dirs:
        Directory names to skip entirely (defaults to common build/test dirs).
    test_classes_kept:
        When ``False`` (default), files under any directory named ``test`` or
        ``tests`` are skipped — production-class focus matches the framework's
        decomposition target.
    """

    root: Path
    excluded_dirs: frozenset[str] = frozenset({
        "target", "build", ".gradle", ".mvn", "node_modules", ".git",
        ".idea", ".vscode", "out", "bin", "dist",
    })
    test_classes_kept: bool = False

    def __iter__(self) -> Iterator[SourceFile]:
        if not self.root.is_dir():
            raise FileNotFoundError(f"Codebase root not found: {self.root}")
        for path in self._iter_java_files(self.root):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Some legacy files may not be utf-8; skip rather than fail.
                continue
            package = self._extract_package(text)
            types = tuple(self._extract_types(text))
            yield SourceFile(path=path, package=package, types=types, text=text)

    # ------------------------------------------------------------------
    def _iter_java_files(self, root: Path) -> Iterator[Path]:
        for path in root.rglob("*.java"):
            parts_lower = [p.lower() for p in path.relative_to(root).parts]
            if any(p in self.excluded_dirs for p in parts_lower):
                continue
            if not self.test_classes_kept and ("test" in parts_lower or "tests" in parts_lower):
                continue
            yield path

    @staticmethod
    def _extract_package(text: str) -> str:
        m = _PACKAGE_RE.search(text)
        return m.group(1) if m else ""

    @staticmethod
    def _extract_types(text: str) -> Iterable[tuple[str, str]]:
        for m in _TYPE_RE.finditer(text):
            yield (m.group(1), m.group(2))


def walk_codebase(root: Path) -> list[SourceFile]:
    """Eagerly walk *root* and return every Java source file."""
    return list(SourceWalker(root=root))


# ----------------------------------------------------------------------
# Stereotype detection (heuristic, used by deterministic A2 views)
# ----------------------------------------------------------------------

_STEREOTYPE_SUFFIXES: tuple[tuple[str, str], ...] = (
    ("Controller",   "controller"),
    ("RestController", "controller"),
    ("Resource",     "controller"),
    ("Servlet",      "controller"),
    ("Endpoint",     "controller"),
    ("Action",       "controller"),
    ("ActionBean",   "controller"),
    ("Service",      "service"),
    ("ServiceImpl",  "service"),
    ("Manager",      "service"),
    ("Facade",       "service"),
    ("Repository",   "repository"),
    ("Dao",          "repository"),
    ("DAO",          "repository"),
    ("Mapper",       "repository"),
    ("Entity",       "entity"),
    ("DTO",          "dto"),
    ("Dto",          "dto"),
    ("Request",      "dto"),
    ("Response",     "dto"),
    ("Config",       "config"),
    ("Configuration","config"),
    ("Util",         "util"),
    ("Utils",        "util"),
    ("Helper",       "util"),
    ("Exception",    "exception"),
    ("Listener",     "infrastructure"),
    ("Filter",       "infrastructure"),
)


def detect_stereotypes(class_name: str, package: str) -> list[str]:
    """Return zero or more heuristic stereotype labels for a class."""
    labels: list[str] = []
    for suffix, label in _STEREOTYPE_SUFFIXES:
        if class_name.endswith(suffix):
            labels.append(label)
            break
    pkg_lower = package.lower()
    if "controller" in pkg_lower and "controller" not in labels:
        labels.append("controller")
    if "service" in pkg_lower and "service" not in labels:
        labels.append("service")
    if "repository" in pkg_lower or ".dao" in pkg_lower or "mapper" in pkg_lower:
        if "repository" not in labels:
            labels.append("repository")
    if "domain" in pkg_lower or ".model" in pkg_lower or "entity" in pkg_lower:
        if not any(l in labels for l in ("entity", "dto")):
            labels.append("entity")
    if "config" in pkg_lower and "config" not in labels:
        labels.append("config")
    return labels
