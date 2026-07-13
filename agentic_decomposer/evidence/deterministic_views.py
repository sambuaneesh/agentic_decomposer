"""Derive A2 (components), A3 (API endpoints), and A4 (technology map)
from the raw codebase without calling an LLM.

These deterministic views are used when ``--evidence-mode deterministic``
is passed. A1 (component diagram) and A5 (dynamic interactions) are best
expressed synthetically and remain ``None`` in this mode (the LLM mode
fills them in instead).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from agentic_decomposer.evidence.source_walker import (
    SourceFile,
    detect_stereotypes,
)


# ----------------------------------------------------------------------
# A2 — Component overview table (group classes by package prefix)
# ----------------------------------------------------------------------

def derive_components(files: list[SourceFile]) -> list[dict]:
    """Group classes by their package prefix (everything before the last segment)."""
    groups: dict[str, list[SourceFile]] = {}
    for sf in files:
        if not sf.primary_type:
            continue
        key = sf.package or "(default)"
        groups.setdefault(key, []).append(sf)

    components: list[dict] = []
    for package, members in sorted(groups.items()):
        # All classes in the same package usually share a stereotype focus.
        stereotype_votes: dict[str, int] = {}
        class_names: list[str] = []
        for sf in members:
            kind, simple_name = sf.primary_type  # type: ignore[misc]
            class_names.append(simple_name)
            for s in detect_stereotypes(simple_name, package):
                stereotype_votes[s] = stereotype_votes.get(s, 0) + 1
        if stereotype_votes:
            comp_type = max(stereotype_votes.items(), key=lambda kv: kv[1])[0]
        else:
            comp_type = None
        components.append({
            "name": _component_name(package),
            "type": comp_type,
            "classes": class_names,
            "responsibilities": [
                f"Classes in package {package} ({len(class_names)} types)."
            ],
            "package_prefix": package,
        })
    return components


def _component_name(package: str) -> str:
    if not package or package == "(default)":
        return "DefaultPackage"
    last = package.rsplit(".", 1)[-1]
    return last.capitalize() if last else package


# ----------------------------------------------------------------------
# A3 — API endpoints
# ----------------------------------------------------------------------

_SPRING_METHOD_ANNOTATIONS = {
    "GetMapping":    "GET",
    "PostMapping":   "POST",
    "PutMapping":    "PUT",
    "PatchMapping":  "PATCH",
    "DeleteMapping": "DELETE",
}

_SPRING_REQUEST_MAPPING_RE = re.compile(
    r"@RequestMapping\s*\(\s*([^)]*)\)", re.MULTILINE,
)

_JAXRS_METHOD_ANNOTATIONS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}

_PATH_ANNOTATION_RE = re.compile(r"@Path\s*\(\s*([^)]+)\s*\)")
_VALUE_ATTR_RE = re.compile(r'(?:value|path)\s*=\s*"([^"]+)"')
_BARE_STRING_RE = re.compile(r'"([^"]+)"')
_METHOD_ATTR_RE = re.compile(r"method\s*=\s*(?:RequestMethod\.)?(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)")


def derive_api_endpoints(files: list[SourceFile]) -> list[dict]:
    """Scan Spring / JAX-RS / Servlet annotations for endpoints."""
    endpoints: list[dict] = []
    for sf in files:
        if not sf.primary_type:
            continue
        _, class_name = sf.primary_type
        # Class-level @RequestMapping or @Path becomes the path prefix.
        class_prefix = _class_prefix(sf.text)
        for annotation, http_method in _SPRING_METHOD_ANNOTATIONS.items():
            for path in _find_paths(sf.text, f"@{annotation}"):
                endpoints.append({
                    "method": http_method,
                    "path": _join_paths(class_prefix, path),
                    "handler_class": class_name,
                    "handler_method": None,
                    "related_entities": [],
                })
        # @RequestMapping(method=POST, value="/x")
        for m in _SPRING_REQUEST_MAPPING_RE.finditer(sf.text):
            args = m.group(1)
            method_match = _METHOD_ATTR_RE.search(args)
            http_method = method_match.group(1) if method_match else "ANY"
            for path in _path_attrs(args):
                endpoints.append({
                    "method": http_method,
                    "path": _join_paths(class_prefix, path),
                    "handler_class": class_name,
                    "handler_method": None,
                    "related_entities": [],
                })
        # JAX-RS: method annotations (@GET etc.) paired with @Path
        for jaxrs in _JAXRS_METHOD_ANNOTATIONS:
            if f"@{jaxrs}" in sf.text:
                for path in _find_paths(sf.text, "@Path"):
                    endpoints.append({
                        "method": jaxrs,
                        "path": _join_paths(class_prefix, path),
                        "handler_class": class_name,
                        "handler_method": None,
                        "related_entities": [],
                    })
                break
    # Deduplicate
    seen = set()
    unique: list[dict] = []
    for ep in endpoints:
        key = (ep["method"], ep["path"], ep["handler_class"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(ep)
    return unique


def _class_prefix(text: str) -> str:
    m = _SPRING_REQUEST_MAPPING_RE.search(text)
    if not m:
        # Try @Path on class
        path_m = _PATH_ANNOTATION_RE.search(text)
        return _strip_quotes(path_m.group(1)) if path_m else ""
    return next(iter(_path_attrs(m.group(1))), "")


def _path_attrs(args: str) -> list[str]:
    paths = [m.group(1) for m in _VALUE_ATTR_RE.finditer(args)]
    if paths:
        return paths
    # bare string argument
    bare = _BARE_STRING_RE.search(args)
    return [bare.group(1)] if bare else []


def _find_paths(text: str, annotation: str) -> list[str]:
    pattern = re.compile(
        re.escape(annotation) + r"\s*\(\s*([^)]+)\)",
    )
    out: list[str] = []
    for m in pattern.finditer(text):
        out.extend(_path_attrs(m.group(1)))
    return out


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1]
    return s


def _join_paths(prefix: str, suffix: str) -> str:
    p = (prefix or "").rstrip("/")
    s = (suffix or "").lstrip("/")
    if not p:
        return "/" + s if s else "/"
    if not s:
        return p
    return f"{p}/{s}"


# ----------------------------------------------------------------------
# A4 — Technology map
# ----------------------------------------------------------------------

def derive_technology_map(repo_root: Path) -> dict:
    """Sniff build files for the high-level technology landscape."""
    tech: dict = {
        "framework": None,
        "language": "Java",
        "database": None,
        "build": None,
        "container": None,
        "other": [],
    }

    if (repo_root / "pom.xml").is_file():
        tech["build"] = "Maven"
        tech.update(_sniff_pom(repo_root / "pom.xml"))
    elif (repo_root / "build.gradle").is_file() or (repo_root / "build.gradle.kts").is_file():
        tech["build"] = "Gradle"
        gradle_file = (
            repo_root / "build.gradle"
            if (repo_root / "build.gradle").is_file()
            else repo_root / "build.gradle.kts"
        )
        tech.update(_sniff_gradle(gradle_file))

    if (repo_root / "Dockerfile").is_file():
        tech["container"] = "Docker"
    elif (repo_root / "docker-compose.yaml").is_file() or (repo_root / "docker-compose.yml").is_file():
        tech["container"] = "Docker Compose"
    return tech


_POM_FRAMEWORK_HINTS = (
    ("spring-boot",       "Spring Boot"),
    ("springframework",   "Spring"),
    ("mybatis",           "MyBatis"),
    ("jakarta.servlet",   "Java EE / Jakarta"),
    ("stripes",           "Stripes"),
    ("dropwizard",        "Dropwizard"),
    ("micronaut",         "Micronaut"),
    ("quarkus",           "Quarkus"),
)

_POM_DB_HINTS = (
    ("h2",                "H2"),
    ("hsqldb",            "HSQLDB"),
    ("mysql",             "MySQL"),
    ("postgresql",        "PostgreSQL"),
    ("oracle",            "Oracle"),
    ("mssql",             "MSSQL"),
)


def _sniff_pom(pom: Path) -> dict:
    text = pom.read_text(encoding="utf-8", errors="ignore").lower()
    out: dict = {}
    for needle, label in _POM_FRAMEWORK_HINTS:
        if needle in text:
            out["framework"] = label
            break
    for needle, label in _POM_DB_HINTS:
        if needle in text:
            out["database"] = label
            break
    return out


def _sniff_gradle(gradle: Path) -> dict:
    text = gradle.read_text(encoding="utf-8", errors="ignore").lower()
    out: dict = {}
    if "org.springframework.boot" in text:
        out["framework"] = "Spring Boot"
    elif "org.springframework" in text:
        out["framework"] = "Spring"
    for needle, label in _POM_DB_HINTS:
        if needle in text:
            out["database"] = label
            break
    return out


# ----------------------------------------------------------------------
# Persistence entities (used by Evidence Constructor regardless of mode)
# ----------------------------------------------------------------------

_ENTITY_ANNOTATIONS = ("@Entity", "@Table", "@Document", "@Aggregate", "@Mapper")


def derive_persistence_entities(files: list[SourceFile]) -> list[dict]:
    """Detect classes annotated as JPA/MyBatis/Spring Data entities."""
    out: list[dict] = []
    for sf in files:
        if not any(a in sf.text for a in _ENTITY_ANNOTATIONS):
            continue
        ty = sf.primary_type
        if not ty:
            continue
        _, name = ty
        table = _extract_table_name(sf.text) or name.lower()
        # Look for a sibling repository / mapper interface
        repo = _find_repository(files, name)
        out.append({
            "entity": name,
            "repository": repo,
            "tables": [table],
        })
    return out


_TABLE_RE = re.compile(r'@Table\s*\(\s*name\s*=\s*"([^"]+)"')


def _extract_table_name(text: str) -> str | None:
    m = _TABLE_RE.search(text)
    return m.group(1) if m else None


def _find_repository(files: list[SourceFile], entity_name: str) -> str | None:
    candidates = (
        f"{entity_name}Repository",
        f"{entity_name}Mapper",
        f"{entity_name}Dao",
        f"{entity_name}DAO",
    )
    for sf in files:
        ty = sf.primary_type
        if not ty:
            continue
        _, name = ty
        if name in candidates:
            return name
    return None
