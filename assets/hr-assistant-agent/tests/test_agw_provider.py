"""Tests for mcp_providers/agw.py module (IBD_TESTING mode)."""
import asyncio
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

# IBD_TESTING is set by conftest.py


class TestGetMcpToolsTestingMode:
    """Tests for get_mcp_tools() in IBD_TESTING mode."""

    def test_returns_list(self):
        from mcp_providers.agw import get_mcp_tools
        tools = asyncio.run(get_mcp_tools())
        assert isinstance(tools, list)

    def test_returns_non_empty_list_with_mock(self):
        """With a valid mcp-mock.json, should return tools."""
        from mcp_providers.agw import get_mcp_tools
        tools = asyncio.run(get_mcp_tools())
        assert len(tools) > 0

    def test_tools_are_callable(self):
        """Each returned tool should be callable (LangChain tool)."""
        from mcp_providers.agw import get_mcp_tools
        tools = asyncio.run(get_mcp_tools())
        for tool in tools:
            assert callable(tool) or hasattr(tool, "invoke") or hasattr(tool, "_run")

    def test_tools_have_names(self):
        """Each tool should have a non-empty name."""
        from mcp_providers.agw import get_mcp_tools
        tools = asyncio.run(get_mcp_tools())
        for tool in tools:
            assert hasattr(tool, "name")
            assert tool.name  # non-empty


class TestGetUserSub:
    """Tests for get_user_sub() function."""

    def test_returns_string_in_testing_mode_without_token(self):
        """In IBD_TESTING mode without token, get_user_sub() returns 'unknown'."""
        from mcp_providers.agw import get_user_sub
        # IBD_TESTING=1 is set — no token in context so returns 'unknown'
        result = get_user_sub()
        assert isinstance(result, str)
        assert result == "unknown"

    def test_returns_sub_from_valid_jwt(self):
        """get_user_sub() should decode sub claim from a valid JWT."""
        import base64
        import json as _json
        from mcp_providers.agw import set_user_token, reset_user_token, get_user_sub

        # Build a minimal fake JWT (not signed)
        header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').decode().rstrip("=")
        payload = base64.urlsafe_b64encode(
            _json.dumps({"sub": "test-user-123"}).encode()
        ).decode().rstrip("=")
        fake_jwt = f"{header}.{payload}.fakesig"

        ctx_token = set_user_token(fake_jwt)
        try:
            result = get_user_sub()
            assert result == "test-user-123"
        finally:
            reset_user_token(ctx_token)


class TestSetUserToken:
    """Tests for set_user_token() function."""

    def test_set_and_get_user_token(self):
        """set_user_token and get_user_token should round-trip."""
        from mcp_providers.agw import set_user_token, get_user_token, reset_user_token
        ctx_token = set_user_token("test-jwt-token")
        try:
            assert get_user_token() == "test-jwt-token"
        finally:
            reset_user_token(ctx_token)

    def test_reset_clears_token(self):
        """reset_user_token should restore token to previous value."""
        from mcp_providers.agw import set_user_token, get_user_token, reset_user_token
        # Initially None
        initial = get_user_token()
        ctx_token = set_user_token("some-token")
        assert get_user_token() == "some-token"
        reset_user_token(ctx_token)
        # After reset, should be back to initial value (None)
        assert get_user_token() == initial
