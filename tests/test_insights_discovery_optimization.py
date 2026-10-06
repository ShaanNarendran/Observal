# SPDX-FileCopyrightText: 2026 Observal Contributors
# SPDX-FileCopyrightText: 2026 Shaan Narendran <shaannaren06@gmail.com>
# SPDX-License-Identifier: Apache-2.0

"""ARD advice uses the selected listing and aggregate session evidence only."""

import json
from types import SimpleNamespace

import pytest
import pytest_asyncio

from services.insights import discovery_optimization as optimizer
from tests import discovery_support as fx


@pytest_asyncio.fixture()
async def sessions():
    engine = fx.make_engine()
    try:
        yield await fx.create_schema(engine)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_agent_suggestions_use_versioned_ard_and_aggregate_signals(sessions, monkeypatch):
    async def setting(*_args):
        return "test/model"

    monkeypatch.setattr("services.dynamic_settings.get", setting)
    prompts = []

    async def model(prompt, **_kwargs):
        prompts.append(prompt)
        return {
            "suggestions": [
                {
                    "illustrative_query": "security vulnerability pull request review",
                    "suggested_description": "Reviews pull requests for security vulnerabilities using GitHub and a review skill.",
                    "rationale": "Clarify the review focus already supported by the linked skill.",
                    "evidence_keys": ["total_sessions"],
                }
            ]
        }

    monkeypatch.setattr(optimizer, "get_call_model", lambda: model)
    async with sessions() as db:
        owner = await fx.user(db)
        skill = await fx.skill(db, owner)
        agent = await fx.agent(db, owner, components=[("skill", skill.id, "Security Review")])
        from models.agent import AgentVersion

        version = await db.get(AgentVersion, agent.latest_version_id)
        version.description = "Helps with development tasks."
        await db.flush()
        report = SimpleNamespace(subject_type="agent", agent_id=agent.id, agent_version_id=agent.latest_version_id)
        result = await optimizer.generate_discovery_optimization(
            db,
            report,
            {
                "metrics": {"rich": {"total_sessions": 5, "tool_errors": 2, "top_tools": [("secret-command", 99)]}},
                "facets_summary": {
                    "goal_categories": [("write_tests", 3), ("PRIVATE CONSUMER PROMPT", 7)],
                    "repeated_instructions": [{"instruction": "PRIVATE CONSUMER PROMPT", "frequency": 7}],
                },
            },
        )
    assert result["status"] == "generated"
    assert result["session_signals"] == {"total_sessions": 5, "tool_errors": 2, "goal:write_tests": 3}
    assert result["suggestions"][0]["field"] == "description"
    assert result["suggestions"][0]["relevance_after"] >= result["suggestions"][0]["relevance_before"]
    assert "secret-command" not in prompts[0]
    assert "PRIVATE CONSUMER PROMPT" not in prompts[0]
    assert "5" in prompts[0]
    assert "You are a meticulous reviewer" not in prompts[0]


@pytest.mark.asyncio
async def test_component_suggestions_never_send_consumer_text_or_unsupported_metrics(sessions, monkeypatch):
    async def setting(*_args):
        return "test/model"

    monkeypatch.setattr("services.dynamic_settings.get", setting)
    prompts = []

    async def model(prompt, **_kwargs):
        prompts.append(prompt)
        return {
            "suggestions": [
                {
                    "illustrative_query": "review code for authentication bugs",
                    "suggested_description": "Reviews code changes for authentication and authorization vulnerabilities.",
                    "rationale": "Specify the existing skill's security-review task more clearly.",
                    "evidence_keys": ["observed_calls"],  # not a skill evidence field
                }
            ]
        }

    monkeypatch.setattr(optimizer, "get_call_model", lambda: model)
    async with sessions() as db:
        owner = await fx.user(db)
        skill = await fx.skill(db, owner)
        report = SimpleNamespace(
            subject_type="component",
            component_type="skill",
            component_id=skill.id,
            component_version_id=skill.latest_version_id,
        )
        result = await optimizer.generate_discovery_optimization(
            db,
            report,
            {
                "metrics": {"present_sessions": 4, "loaded_sessions": 2, "observed_calls": 999},
                "narrative": {"summary": "PRIVATE CONSUMER PROMPT"},
            },
        )
    assert result["status"] == "generated"
    assert result["suggestions"] == []  # cannot cite a signal this extractor did not observe
    data = json.loads(prompts[0].split("UNTRUSTED LISTING DATA:\n", 1)[1])
    assert data["session_signals"] == {"present_sessions": 4, "loaded_sessions": 2}
    assert "PRIVATE CONSUMER PROMPT" not in prompts[0]
    assert "999" not in prompts[0]


@pytest.mark.asyncio
async def test_unsupported_claims_are_not_published(sessions, monkeypatch):
    async def setting(*_args):
        return "test/model"

    async def model(*_args, **_kwargs):
        return {
            "suggestions": [
                {
                    "illustrative_query": "automated security review",
                    "suggested_description": "Automatically guarantees compliant and efficient security reviews.",
                    "rationale": "This will increase traffic for the listing.",
                    "evidence_keys": [],
                }
            ]
        }

    monkeypatch.setattr("services.dynamic_settings.get", setting)
    monkeypatch.setattr(optimizer, "get_call_model", lambda: model)
    async with sessions() as db:
        owner = await fx.user(db)
        agent = await fx.agent(db, owner)
        report = SimpleNamespace(subject_type="agent", agent_id=agent.id, agent_version_id=agent.latest_version_id)
        result = await optimizer.generate_discovery_optimization(db, report, {"metrics": {"rich": {}}})
    assert result["status"] == "generated"
    assert result["suggestions"] == []


def test_request_flag_is_opt_in():
    from schemas.insights import GenerateComponentInsightRequest, GenerateInsightRequest

    assert not GenerateInsightRequest().include_discovery_optimization
    assert not GenerateComponentInsightRequest().include_discovery_optimization
    assert GenerateInsightRequest(include_discovery_optimization=True).include_discovery_optimization
    assert GenerateComponentInsightRequest(include_discovery_optimization=True).include_discovery_optimization


@pytest.mark.asyncio
async def test_model_not_configured_returns_unavailable_without_call(sessions, monkeypatch):
    async def setting(*_args):
        return ""

    monkeypatch.setattr("services.dynamic_settings.get", setting)
    monkeypatch.setattr(optimizer, "get_call_model", lambda: pytest.fail("model should not be called"))
    async with sessions() as db:
        owner = await fx.user(db)
        agent = await fx.agent(db, owner)
        report = SimpleNamespace(subject_type="agent", agent_id=agent.id, agent_version_id=agent.latest_version_id)
        result = await optimizer.generate_discovery_optimization(db, report, {"metrics": {"rich": {}}})
    assert result == {"status": "unavailable", "reason": "model_not_configured"}


@pytest.mark.asyncio
async def test_optional_enrichment_failure_does_not_fail_report(monkeypatch):
    from services.insights import batch

    async def broken(*_args):
        raise RuntimeError("secret prompt from provider")

    monkeypatch.setattr(optimizer, "generate_discovery_optimization", broken)
    report = SimpleNamespace(discovery_optimization_requested=True, discovery_optimization=None)
    await batch._add_discovery_optimization(None, report, {})
    assert report.discovery_optimization == {"status": "unavailable", "reason": "generation_failed"}
    report.discovery_optimization_requested = False
    report.discovery_optimization = None
    await batch._add_discovery_optimization(None, report, {})
    assert report.discovery_optimization is None
