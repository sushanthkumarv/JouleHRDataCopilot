"""Tests for a2a_client module."""
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from a2a_client import (
    A2AAuthorizationError,
    A2AClientError,
    fetch_document,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(status_code: int, body: dict) -> httpx.Response:
    """Build a fake httpx.Response."""
    request = httpx.Request("POST", "http://external-agent:8080/")
    return httpx.Response(
        status_code=status_code,
        content=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
        request=request,
    )


# ---------------------------------------------------------------------------
# Endpoint configuration
# ---------------------------------------------------------------------------

class TestEndpointConfig:
    @pytest.mark.asyncio
    async def test_missing_endpoint_raises(self, monkeypatch):
        monkeypatch.delenv("EXTERNAL_AVIATOR_AGENT_ENDPOINT", raising=False)
        with pytest.raises(A2AClientError, match="EXTERNAL_AVIATOR_AGENT_ENDPOINT"):
            await fetch_document("user1", "payslip", {})


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------

class TestFetchDocumentSuccess:
    @pytest.fixture(autouse=True)
    def set_env(self, monkeypatch):
        monkeypatch.setenv("EXTERNAL_AVIATOR_AGENT_ENDPOINT", "http://external-agent:8080")

    @pytest.mark.asyncio
    async def test_returns_artifacts_on_success(self):
        mock_resp = _make_response(200, {
            "result": {
                "artifacts": [{"type": "pdf", "content": "base64content"}]
            }
        })
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
            result = await fetch_document("user1", "payslip", {"period": "2024-01"})
        assert "artifacts" in result
        assert len(result["artifacts"]) == 1

    @pytest.mark.asyncio
    async def test_request_id_is_generated_if_not_provided(self):
        mock_resp = _make_response(200, {
            "result": {"artifacts": [{"type": "pdf"}]}
        })
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
            result = await fetch_document("user1", "payslip", {})
        assert "request_id" in result


# ---------------------------------------------------------------------------
# Authorization error
# ---------------------------------------------------------------------------

class TestFetchDocumentAuthError:
    @pytest.fixture(autouse=True)
    def set_env(self, monkeypatch):
        monkeypatch.setenv("EXTERNAL_AVIATOR_AGENT_ENDPOINT", "http://external-agent:8080")

    @pytest.mark.asyncio
    async def test_raises_auth_error_on_401(self):
        mock_resp = _make_response(401, {"error": "Unauthorized"})
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(A2AAuthorizationError):
                await fetch_document("user1", "payslip", {})

    @pytest.mark.asyncio
    async def test_raises_auth_error_on_403(self):
        mock_resp = _make_response(403, {"error": "Forbidden"})
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(A2AAuthorizationError):
                await fetch_document("user1", "payslip", {})

    @pytest.mark.asyncio
    async def test_auth_error_not_retried(self):
        """Auth errors should propagate immediately without retries."""
        mock_resp = _make_response(401, {"error": "Unauthorized"})
        mock_post = AsyncMock(return_value=mock_resp)
        with patch("httpx.AsyncClient.post", mock_post):
            with pytest.raises(A2AAuthorizationError):
                await fetch_document("user1", "payslip", {})
        # Should only be called once — no retries
        assert mock_post.call_count == 1


# ---------------------------------------------------------------------------
# Retry and failure
# ---------------------------------------------------------------------------

class TestFetchDocumentRetry:
    @pytest.fixture(autouse=True)
    def set_env(self, monkeypatch):
        monkeypatch.setenv("EXTERNAL_AVIATOR_AGENT_ENDPOINT", "http://external-agent:8080")

    @pytest.mark.asyncio
    async def test_retries_on_timeout(self):
        """Should retry up to _MAX_RETRIES times on TimeoutException."""
        mock_post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        with patch("httpx.AsyncClient.post", mock_post):
            with patch("asyncio.sleep", new_callable=AsyncMock):  # skip real sleep
                with pytest.raises(A2AClientError):
                    await fetch_document("user1", "payslip", {})
        # 1 initial + 2 retries = 3 calls
        assert mock_post.call_count == 3

    @pytest.mark.asyncio
    async def test_raises_client_error_after_all_retries(self):
        mock_post = AsyncMock(side_effect=httpx.ConnectError("refused"))
        with patch("httpx.AsyncClient.post", mock_post):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(A2AClientError):
                    await fetch_document("user1", "payslip", {})

    @pytest.mark.asyncio
    async def test_succeeds_on_second_attempt(self):
        success_resp = _make_response(200, {
            "result": {"artifacts": [{"type": "pdf"}]}
        })
        mock_post = AsyncMock(side_effect=[
            httpx.TimeoutException("timeout"),
            success_resp,
        ])
        with patch("httpx.AsyncClient.post", mock_post):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await fetch_document("user1", "payslip", {})
        assert "artifacts" in result
        assert mock_post.call_count == 2


# ---------------------------------------------------------------------------
# Empty payload handling
# ---------------------------------------------------------------------------

class TestFetchDocumentEmptyPayload:
    @pytest.fixture(autouse=True)
    def set_env(self, monkeypatch):
        monkeypatch.setenv("EXTERNAL_AVIATOR_AGENT_ENDPOINT", "http://external-agent:8080")

    @pytest.mark.asyncio
    async def test_raises_on_empty_payload_after_retries(self):
        """Should raise A2AClientError if response has no artifacts."""
        empty_resp = _make_response(200, {"result": {"artifacts": []}})
        mock_post = AsyncMock(return_value=empty_resp)
        with patch("httpx.AsyncClient.post", mock_post):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(A2AClientError):
                    await fetch_document("user1", "payslip", {})
