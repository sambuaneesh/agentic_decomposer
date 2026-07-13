"""Architectural Evidence Constructor agent.

Stage 3 of the MVP roadmap. Composes ``evidence_pack.json`` for one run.

Modes:

* ``llm``           — Phase-1 summarisation → LLM call → A1..A5 + A6.
* ``deterministic`` — Static parsing → A2/A3/A4 + A6 (A1, A5 left null).
* ``external``      — Load A1..A5 from disk + A6 from graph-artifacts.

A6 is always loaded from ``graph-artifacts/<system>-class-dependency.json``
and merged with the chosen view source. Stable IDs (C001, K_001, …) are
minted here so every downstream artifact can reference them.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentic_decomposer.agents.base import AgentResult, BaseAgent
from agentic_decomposer.artifacts.ids import IdMinter
from agentic_decomposer.artifacts.validators import validate
from agentic_decomposer.evidence.dependency_graph_loader import (
    DependencyGraphData,
    load_dependency_graph,
)
from agentic_decomposer.evidence.deterministic_views import (
    derive_api_endpoints,
    derive_components,
    derive_persistence_entities,
    derive_technology_map,
)
from agentic_decomposer.evidence.external_views import (
    ExternalViews,
    load_external_views,
)
from agentic_decomposer.evidence.llm_views import LLMViews, generate_llm_views
from agentic_decomposer.evidence.source_walker import (
    SourceFile,
    detect_stereotypes,
    walk_codebase,
)
from agentic_decomposer.evidence.summariser import (
    SummariserConfig,
    summarise_codebase,
)
from agentic_decomposer.llm.client import LLMClient, LLMConfig
from agentic_decomposer.paths import codebase_path
from agentic_decomposer.runs import write_json


class EvidenceConstructorAgent(BaseAgent):
    """Build the ``evidence_pack.json`` artifact for one run."""

    name = "evidence_constructor"

    def _run(self, **_: Any) -> AgentResult:
        repo_root = codebase_path(self.config.system)
        sources = walk_codebase(repo_root)
        self.logger.info("evidence.sources_walked count=%d root=%s",
                         len(sources), repo_root)

        # A6 is always deterministic.
        dep_graph = load_dependency_graph(self.config.system)

        # Build the per-class inventory from the union of static graph + source walk.
        classes_payload, class_id_index = self._build_classes(dep_graph, sources)

        # Pick the view-source mode.
        mode = self.config.evidence_mode
        llm_views: LLMViews | None = None
        external: ExternalViews | None = None
        source_summary: str | None = None
        tokens_used = 0

        if mode == "llm":
            source_summary, summary_tokens = self._summarise(sources)
            tokens_used += summary_tokens
            llm_views = self._call_llm_views(source_summary, dep_graph)
            tokens_used += llm_views.tokens_used
            components_raw     = llm_views.components
            api_endpoints_raw  = llm_views.api_endpoints
            technology_map_raw = llm_views.technology_map
            dynamic_raw        = llm_views.dynamic_interactions
            persistence_raw    = llm_views.persistence_entities
            component_diagram  = llm_views.component_diagram
        elif mode == "deterministic":
            components_raw     = derive_components(sources)
            api_endpoints_raw  = derive_api_endpoints(sources)
            technology_map_raw = derive_technology_map(repo_root)
            dynamic_raw        = []
            persistence_raw    = derive_persistence_entities(sources)
            component_diagram  = None
        elif mode == "external":
            if not self.config.external_views_dir:
                raise ValueError("evidence_mode='external' requires external_views_dir")
            external = load_external_views(Path(self.config.external_views_dir),
                                           self.config.system)
            components_raw     = external.components
            api_endpoints_raw  = external.api_endpoints
            technology_map_raw = external.technology_map
            dynamic_raw        = external.dynamic_interactions
            persistence_raw    = derive_persistence_entities(sources)
            component_diagram  = external.component_diagram
        else:
            raise ValueError(f"Unknown evidence_mode {mode!r}")

        # Mint stable IDs across all view collections.
        minter = IdMinter()
        components_payload    = _mint_components(components_raw, minter)
        api_payload           = _mint_api_endpoints(api_endpoints_raw, minter)
        persistence_payload   = _normalise_persistence(persistence_raw)
        dynamic_payload       = _mint_dynamic(dynamic_raw, minter)
        edges_payload         = _mint_edges(dep_graph, minter)
        technology_payload    = _normalise_technology(technology_map_raw)

        payload = {
            "system": self.config.system,
            "evidence_mode": mode,
            "source_summary": source_summary,
            "classes": classes_payload,
            "components": components_payload,
            "api_endpoints": api_payload,
            "persistence_entities": persistence_payload,
            "dependency_edges": edges_payload,
            "dynamic_interactions": dynamic_payload,
            "technology_map": technology_payload,
            "component_diagram": component_diagram,
            "metadata": {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "evidence_mode": mode,
                "model": self.config.model if mode == "llm" else None,
                "tokens_used": int(tokens_used),
                "source_file_count": len(sources),
                "static_graph_class_count": len(dep_graph.classes),
            },
        }
        validate(payload, "evidence_pack")
        write_json(self.layout.evidence_pack_path, payload)

        # Side artifacts for traceability.
        if llm_views is not None and source_summary is not None:
            write_json(self.layout.evidence_dir / "summarisation_meta.json", {
                "strategy": self.config.summarisation_strategy,
                "summary_characters": len(source_summary),
                "model": self.config.model,
                "tokens_used": int(tokens_used),
            })
            write_json(self.layout.evidence_dir / "raw_llm_views.json", {
                "component_diagram":    llm_views.component_diagram,
                "components":           llm_views.components,
                "api_endpoints":        llm_views.api_endpoints,
                "technology_map":       llm_views.technology_map,
                "dynamic_interactions": llm_views.dynamic_interactions,
                "persistence_entities": llm_views.persistence_entities,
            })
        if external is not None:
            write_json(self.layout.evidence_dir / "external_views_source.json", {
                "external_views_dir": self.config.external_views_dir,
                "loaded_files": external.loaded_files,
            })
        if mode == "deterministic":
            write_json(self.layout.evidence_dir / "deterministic_views.json", {
                "components": components_raw,
                "api_endpoints": api_endpoints_raw,
                "technology_map": technology_map_raw,
                "persistence_entities": persistence_raw,
            })

        return AgentResult(
            name=self.name, output=payload,
            output_path=str(self.layout.evidence_pack_path),
            tokens_used=tokens_used,
            extras={"class_id_index": class_id_index},
        )

    # ------------------------------------------------------------------
    def _summarise(self, sources: list[SourceFile]) -> tuple[str, int]:
        cfg = SummariserConfig(
            strategy=self.config.summarisation_strategy,
            llm=self._make_llm_client() if self._summary_needs_llm() else None,
        )
        summary = summarise_codebase(sources, cfg)
        # Per-call token cost is captured in llm_calls.jsonl by the LLM client.
        return summary, 0

    def _summary_needs_llm(self) -> bool:
        s = self.config.summarisation_strategy
        return s.endswith("_aggregate") or s == "hierarchical"

    def _call_llm_views(self, summary: str, dep_graph: DependencyGraphData) -> LLMViews:
        llm = self._make_llm_client()
        return generate_llm_views(
            system=self.config.system,
            summary=summary,
            known_classes=dep_graph.simple_names,
            llm=llm,
        )

    def _make_llm_client(self) -> LLMClient:
        return LLMClient(LLMConfig(
            model=self.config.model,
            seed=self.config.seed,
            log_path=self.layout.llm_calls_log_path,
        ))

    # ------------------------------------------------------------------
    def _build_classes(
        self,
        dep_graph: DependencyGraphData,
        sources: list[SourceFile],
    ) -> tuple[list[dict], dict[str, str]]:
        # Map simple class name → first source file we saw it in.
        by_simple: dict[str, SourceFile] = {}
        for sf in sources:
            ty = sf.primary_type
            if not ty:
                continue
            _, name = ty
            by_simple.setdefault(name, sf)

        minter = IdMinter()
        classes_payload: list[dict] = []
        class_id_index: dict[str, str] = {}
        for node in dep_graph.classes:
            cid = minter.next("class_node")
            sf = by_simple.get(node.simple_name)
            classes_payload.append({
                "id": cid,
                "name": node.simple_name,
                "package": node.package or (sf.package if sf else ""),
                "file_path":
                    str(sf.path.relative_to(codebase_path(self.config.system))).replace("\\", "/")
                    if sf else None,
                "kind": "class",
                "stereotypes": detect_stereotypes(node.simple_name, node.package),
            })
            class_id_index[node.simple_name] = cid
        return classes_payload, class_id_index


# ----------------------------------------------------------------------
# ID minting helpers
# ----------------------------------------------------------------------

def _mint_components(raw: list[dict], minter: IdMinter) -> list[dict]:
    out: list[dict] = []
    for c in raw or []:
        out.append({
            "id":               minter.next("component"),
            "name":             c.get("name") or "UnnamedComponent",
            "type":             c.get("type"),
            "classes":          [_simple(x) for x in (c.get("classes") or [])],
            "responsibilities": list(c.get("responsibilities") or []),
            "package_prefix":   c.get("package_prefix"),
        })
    return out


def _mint_api_endpoints(raw: list[dict], minter: IdMinter) -> list[dict]:
    out: list[dict] = []
    for ep in raw or []:
        method = (ep.get("method") or "ANY").upper()
        if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "ANY"}:
            method = "ANY"
        out.append({
            "id":               minter.next("api"),
            "method":           method,
            "path":             ep.get("path") or "/",
            "handler_class":    _simple(ep.get("handler_class") or "Unknown"),
            "handler_method":   ep.get("handler_method"),
            "related_entities": [_simple(x) for x in (ep.get("related_entities") or [])],
        })
    return out


def _mint_dynamic(raw: list[dict], minter: IdMinter) -> list[dict]:
    out: list[dict] = []
    for sc in raw or []:
        out.append({
            "id":       minter.next("scenario"),
            "scenario": sc.get("scenario") or "Scenario",
            "sequence": [_simple(x) for x in (sc.get("sequence") or [])],
            "trigger":  sc.get("trigger"),
        })
    return out


def _mint_edges(dep_graph: DependencyGraphData, minter: IdMinter) -> list[dict]:
    out: list[dict] = []
    for e in dep_graph.edges:
        out.append({
            "id":     minter.next("edge"),
            "source": e.source_simple,
            "target": e.target_simple,
            "type":   e.type,
            "weight": e.weight,
        })
    return out


def _normalise_persistence(raw: list[dict]) -> list[dict]:
    out: list[dict] = []
    for p in raw or []:
        out.append({
            "entity":     _simple(p.get("entity") or "Entity"),
            "repository": _simple(p["repository"]) if p.get("repository") else None,
            "tables":     list(p.get("tables") or []),
        })
    return out


def _normalise_technology(raw: dict | None) -> dict:
    raw = raw or {}
    return {
        "framework": raw.get("framework"),
        "language":  raw.get("language"),
        "database":  raw.get("database"),
        "build":     raw.get("build"),
        "container": raw.get("container"),
        "other":     list(raw.get("other") or []),
    }


def _simple(name: str | dict) -> str:
    if isinstance(name, dict):
        return str(name.get("id") or name.get("name") or "").rsplit(".", 1)[-1]
    return str(name).rsplit(".", 1)[-1]
