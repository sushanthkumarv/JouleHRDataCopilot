"""Integration test: end-to-end agent flow with mocked LLM and mocked external systems."""
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

# Ensure IBD_TESTING is set so MCP tools use mocks
os.environ["IBD_TESTING"] = "1"


class TestEndToEndAgentFlow:
    """Integration tests: mocked LLM + mocked external systems."""

    @pytest.mark.asyncio
    async def test_agent_stream_returns_response(self):
        """Agent.stream() should yield a final completed response."""
        from agent import SampleAgent

        agent = SampleAgent()

        # Mock the LLM invocation to return a static result
        mock_content = "Your payslip for March 2024 shows a net salary of [REDACTED]."
        mock_message = MagicMock()
        mock_message.content = mock_content

        mock_result = {"messages": [mock_message]}
        with patch.object(agent, "_invoke_with_fallback", new_callable=AsyncMock, return_value=mock_result):
            chunks = []
            async for chunk in agent.stream("Show my payslip", "test-context-001"):
                chunks.append(chunk)

        assert len(chunks) >= 2  # at least processing + final
        final = [c for c in chunks if c.get("is_task_complete")]
        assert len(final) == 1
        assert mock_content in final[0]["content"]

    @pytest.mark.asyncio
    async def test_agent_invoke_returns_completed_status(self):
        """Agent.invoke() should return status=completed on success."""
        from agent import SampleAgent

        agent = SampleAgent()

        mock_message = MagicMock()
        mock_message.content = "Leave balance: 15 days."
        mock_result = {"messages": [mock_message]}

        with patch.object(agent, "_invoke_with_fallback", new_callable=AsyncMock, return_value=mock_result):
            response = await agent.invoke("What is my leave balance?", "test-context-002")

        assert response.status == "completed"
        assert "Leave balance" in response.message

    @pytest.mark.asyncio
    async def test_agent_handles_exception_gracefully(self):
        """Agent.stream() should yield an error chunk on unexpected exceptions."""
        from agent import SampleAgent

        agent = SampleAgent()

        with patch.object(agent, "_invoke_with_fallback", side_effect=RuntimeError("LLM unavailable")):
            chunks = []
            async for chunk in agent.stream("Show employment contract", "test-context-003"):
                chunks.append(chunk)

        error_chunks = [c for c in chunks if c.get("is_task_complete")]
        assert len(error_chunks) >= 1
        assert "error" in error_chunks[-1]["content"].lower() or "encountered" in error_chunks[-1]["content"].lower()

    @pytest.mark.asyncio
    async def test_privacy_redactor_called_correctly(self):
        """Privacy redaction should succeed without raising."""
        from privacy_redactor import apply_redaction
        payslip_data = {
            "gross_salary": "5000",
            "net_salary": "4200",
            "bank_account": "1234567890",
            "tax_id": "123-45-6789",
        }
        ok, result = apply_redaction(payslip_data, "payslip", "employee")
        assert ok
        assert "bank_account" in result
        # Ensure raw bank account not fully exposed
        assert result["bank_account"] != "1234567890"

    @pytest.mark.asyncio
    async def test_audit_log_written_for_interaction(self, tmp_path, monkeypatch):
        """Audit logger should record a full interaction."""
        import audit_logger
        monkeypatch.setenv("AUDIT_LOG_DIR", str(tmp_path / "audit"))
        audit_logger._AUDIT_DIR = str(tmp_path / "audit")
        audit_logger._AUDIT_FILE = str(tmp_path / "audit" / "hr_audit_log.jsonl")

        iid = audit_logger.write_entry(
            user_id="emp001",
            request_summary="Show me my payslip for March",
            authorization_result="granted",
            response_summary="Payslip summary delivered",
            intent_category="payslip",
            data_scope="PAYROLL_VIEW",
            milestone_statuses={
                "M1": "achieved",
                "M2": "achieved",
                "M3": "missed",
                "M4": "achieved",
                "M5": "achieved",
            },
        )
        import json
        log_file = tmp_path / "audit" / "hr_audit_log.jsonl"
        assert log_file.exists()
        entry = json.loads(log_file.read_text().strip())
        assert entry["user_id"] == "emp001"
        assert entry["intent_category"] == "payslip"
        assert entry["milestone_statuses"]["M1"] == "achieved"

    @pytest.mark.asyncio
    async def test_access_denied_flow_no_data_leaked(self):
        """When authorization is denied, no data should appear in the response."""
        from audit_logger import build_access_denied_response
        msg = build_access_denied_response("PAYROLL_VIEW", "payslip")

        # No sensitive data fragments
        for fragment in ["5000", "4200", "bank", "account", "1234"]:
            assert fragment not in msg

    @pytest.mark.asyncio
    async def test_a2a_client_requires_env_var(self, monkeypatch):
        """A2A client must fail with a clear error when endpoint is missing."""
        monkeypatch.delenv("EXTERNAL_AVIATOR_AGENT_ENDPOINT", raising=False)
        from a2a_client import A2AClientError, fetch_document
        with pytest.raises(A2AClientError, match="EXTERNAL_AVIATOR_AGENT_ENDPOINT"):
            await fetch_document("user1", "payslip", {})
