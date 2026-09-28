"""Small flow contract and shared research draft implementation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Protocol

from finagent.contracts import FlowResult, RunStatus, SourceDocument, TaskSpec
from finagent.models import ModelGateway, ModelUnavailable
from finagent.prompts import prompt_for
from finagent.storage import EvidenceStore


@dataclass
class FlowContext:
    task: TaskSpec
    run_id: str
    source_ids: list[str]
    documents: list[SourceDocument]
    ingestion_issues: list[str]
    store: EvidenceStore
    gateway: ModelGateway | None
    model_calls: int = 0
    warnings: list[str] = field(default_factory=list)
    source_metadata: dict[str, dict[str, object]] = field(default_factory=dict)

    def ask_model(self, instruction: str, tier: str = "strong"):
        if self.model_calls >= self.task.max_model_calls:
            raise ModelUnavailable("model call budget exhausted")
        if self.gateway is None:
            raise ModelUnavailable("model gateway is not configured")
        if any(document.data_class.value == "restricted" for document in self.documents):
            raise ModelUnavailable("restricted source cannot be sent to the configured gateway")
        context_parts = []
        for document in self.documents:
            if document.published_at and document.published_at > self.task.as_of:
                continue
            if document.published_at is None:
                self.warnings.append(
                    f"{document.id}: disclosure date is unknown; historical availability is unverified"
                )
            raw = self.store.read_document(document.id)
            try:
                content = raw.decode("utf-8")
            except UnicodeDecodeError:
                self.warnings.append(f"{document.id}: binary source has no text parser")
                continue
            if len(content) > 12000:
                self.warnings.append(f"{document.id}: model context truncated to 12000 characters")
                content = content[:12000]
            context_parts.append(
                f"document_id={document.id}; locator=/; name={document.name}; "
                f"published_at={document.published_at}\n{content}"
            )
        if not context_parts:
            raise ModelUnavailable("no readable source text is available")
        if self.task.question:
            instruction = f"{instruction}\nUser question: {self.task.question}"
        self.model_calls += 1
        self.store.add_event(self.run_id, "model_call", {"tier": tier, "number": self.model_calls})
        return self.gateway.research(instruction, "\n\n".join(context_parts), tier)

    def valid_locator(self, document_id: str, locator: str) -> bool:
        if locator == "/":
            return True
        document = next((item for item in self.documents if item.id == document_id), None)
        if document is None or document.media_type != ".json":
            return False
        try:
            node = json.loads(self.store.read_document(document_id))
            for token in locator.lstrip("/").split("/"):  # JSON Pointer
                token = token.replace("~1", "/").replace("~0", "~")
                node = node[int(token)] if isinstance(node, list) else node[token]
        except (ValueError, KeyError, IndexError, TypeError, json.JSONDecodeError):
            return False
        return True


class Flow(Protocol):
    def execute(self, context: FlowContext) -> FlowResult: ...


class ResearchDraftFlow:
    label = "research"

    def execute(self, context: FlowContext) -> FlowResult:
        try:
            answer = context.ask_model(prompt_for(context.task.line), tier="strong")
        except ModelUnavailable as exc:
            return FlowResult(
                status=RunStatus.BLOCKED,
                payload={"line": self.label, "claims": []},
                limitations=[str(exc), *context.ingestion_issues],
            )
        accepted = [
            claim
            for claim in answer.claims
            if claim.document_id in context.source_ids
            and context.valid_locator(claim.document_id, claim.locator)
        ]
        rejected = len(answer.claims) - len(accepted)
        limitations = [
            *context.ingestion_issues,
            *context.warnings,
            *answer.limitations,
            "research draft requires independent evidence and domain review",
        ]
        if rejected:
            limitations.append(f"{rejected} claim(s) rejected for invalid source locator")
        return FlowResult(
            status=RunStatus.PARTIAL,
            payload={
                "line": self.label,
                "summary": answer.summary,
                "claims": [claim.model_dump(mode="json") for claim in accepted],
            },
            limitations=limitations,
        )
