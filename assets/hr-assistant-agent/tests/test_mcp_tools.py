"""Tests for MCP tool mock loading (IBD_TESTING mode)."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))


class TestMcpToolsTestingMode:
    def test_get_mcp_tools_returns_list_in_testing_mode(self):
        """In IBD_TESTING mode, get_mcp_tools() should return mock tools from mcp-mock.json."""
        import asyncio
        # IBD_TESTING=1 is set by conftest.py
        assert os.environ.get("IBD_TESTING") == "1"
        from mcp_providers.agw import get_mcp_tools
        tools = asyncio.run(get_mcp_tools())
        # Should return a list (possibly empty if no mock file or mock tools)
        assert isinstance(tools, list)

    def test_mcp_mock_json_exists(self):
        """mcp-mock.json must exist for testing."""
        agent_root = Path(__file__).parent.parent
        mock_file = agent_root / "mcp-mock.json"
        assert mock_file.exists(), f"mcp-mock.json not found at {mock_file}"

    def test_mcp_mock_json_valid_structure(self):
        """mcp-mock.json must have the expected structure."""
        import json
        agent_root = Path(__file__).parent.parent
        mock_file = agent_root / "mcp-mock.json"
        with open(mock_file) as f:
            data = json.load(f)
        assert "servers" in data
        assert "metadata" in data
        assert isinstance(data["servers"], dict)
        assert data["metadata"]["mock_mode"] is True

    def test_mcp_mock_json_has_all_6_servers(self):
        """mcp-mock.json must contain all 6 SuccessFactors MCP servers."""
        import json
        agent_root = Path(__file__).parent.parent
        with open(agent_root / "mcp-mock.json") as f:
            data = json.load(f)
        expected_slugs = {
            "pltrolebasedpermissions",
            "ecemployeeprofile",
            "ecemployeecentralpayroll",
            "balances",
            "eccompensationinformation",
            "ecemploymentinformation",
        }
        server_keys = set(data["servers"].keys())
        # Each server key should contain one of the expected slugs
        for slug in expected_slugs:
            assert any(slug in key for key in server_keys), f"Server for {slug} not found in mcp-mock.json"


class TestAuthorizationMcpTool:
    """Tests for PLTRoleBasedPermissions tool (authorization checks)."""

    def test_rbp_server_exists_in_mock(self):
        """PLTRoleBasedPermissions server should be registered in mcp-mock."""
        import json
        agent_root = Path(__file__).parent.parent
        with open(agent_root / "mcp-mock.json") as f:
            data = json.load(f)
        rbp_server = next(
            (v for k, v in data["servers"].items() if "pltrolebasedpermissions" in k),
            None
        )
        assert rbp_server is not None

    def test_rbp_server_has_tools(self):
        """PLTRoleBasedPermissions server should have at least one tool."""
        import json
        agent_root = Path(__file__).parent.parent
        with open(agent_root / "mcp-mock.json") as f:
            data = json.load(f)
        rbp_server = next(
            (v for k, v in data["servers"].items() if "pltrolebasedpermissions" in k),
            None
        )
        assert rbp_server and len(rbp_server["tools"]) > 0


class TestECEmployeeProfileMcpTool:
    """Tests for ECEmployeeProfile tool."""

    def test_ecemployeeprofile_server_has_tools(self):
        import json
        agent_root = Path(__file__).parent.parent
        with open(agent_root / "mcp-mock.json") as f:
            data = json.load(f)
        srv = next(
            (v for k, v in data["servers"].items() if "ecemployeeprofile" in k),
            None
        )
        assert srv and len(srv["tools"]) > 0


class TestECEmployeeCentralPayrollMcpTool:
    """Tests for ECEmployeeCentralPayroll (payslip retrieval) tool."""

    def test_payroll_server_has_tools(self):
        import json
        agent_root = Path(__file__).parent.parent
        with open(agent_root / "mcp-mock.json") as f:
            data = json.load(f)
        srv = next(
            (v for k, v in data["servers"].items() if "ecemployeecentralpayroll" in k),
            None
        )
        assert srv and len(srv["tools"]) > 0


class TestBalancesMcpTool:
    """Tests for Balances (leave balance retrieval) tool."""

    def test_balances_server_has_tools(self):
        import json
        agent_root = Path(__file__).parent.parent
        with open(agent_root / "mcp-mock.json") as f:
            data = json.load(f)
        srv = next(
            (v for k, v in data["servers"].items() if "balances" in k),
            None
        )
        assert srv and len(srv["tools"]) > 0


class TestECCompensationInformationMcpTool:
    """Tests for ECCompensationInformation tool."""

    def test_compensation_server_has_tools(self):
        import json
        agent_root = Path(__file__).parent.parent
        with open(agent_root / "mcp-mock.json") as f:
            data = json.load(f)
        srv = next(
            (v for k, v in data["servers"].items() if "eccompensationinformation" in k),
            None
        )
        assert srv and len(srv["tools"]) > 0


class TestECEmploymentInformationMcpTool:
    """Tests for ECEmploymentInformation tool."""

    def test_employment_info_server_has_tools(self):
        import json
        agent_root = Path(__file__).parent.parent
        with open(agent_root / "mcp-mock.json") as f:
            data = json.load(f)
        srv = next(
            (v for k, v in data["servers"].items() if "ecemploymentinformation" in k),
            None
        )
        assert srv and len(srv["tools"]) > 0
