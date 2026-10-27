"""
A2A Protocol Client for External Document-Generation Agent.

Communicates with the external document-generation agent via the Agent-to-Agent (A2A)
protocol to fetch generated PDF documents or structured data payloads.

Endpoint is configured via the EXTERNAL_AVIATOR_AGENT_ENDPOINT environment variable.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Configuration
_MAX_RETRIES = 2
_RETRY_BASE_DELAY = 1.0  # seconds
_REQUEST_TIMEOUT = 30.0  # seconds


class A2AClientError(Exception):
    """Raised when A2A communication fails after all retries."""


class A2AAuthorizationError(Exception):
    """Raised when A2A endpoint returns an auth/permission error."""


def _get_endpoint() -> str:
    """Read the external agent endpoint from environment."""
    endpoint = os.environ.get("EXTERNAL_AVIATOR_AGENT_ENDPOINT", "")
    if not endpoint:
        raise A2AClientError(
            "EXTERNAL_AVIATOR_AGENT_ENDPOINT environment variable is not set. "
            "Please configure the external document-generation agent endpoint."
        )
    return endpoint.rstrip("/")


async def fetch_document(
    user_id: str,
    intent_category: str,
    data_scope: dict[str, Any],
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Invoke the external document-generation agent via A2A protocol.

    Args:
        user_id: The requesting user's identifier.
        intent_category: The classified HR intent (e.g., 'payslip', 'leave_balance').
        data_scope: Dict containing scope parameters for the document request.
        request_id: Optional correlation ID; generated if not provided.

    Returns:
        Dict containing the document payload or structured data.

    Raises:
        A2AClientError: On communication failure after max retries.
        A2AAuthorizationError: On 401/403 from the external agent.
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    endpoint = _get_endpoint()
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tasks/send",
        "params": {
            "id": request_id,
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "user_id": user_id,
                                "intent_category": intent_category,
                                "data_scope": data_scope,
                            }
                        ),
                    }
                ],
            },
        },
    }

    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
                response = await client.post(
                    f"{endpoint}/",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Request-ID": request_id,
                        "X-User-ID": user_id,
                    },
                )

            if response.status_code in (401, 403):
                raise A2AAuthorizationError(
                    f"External agent returned {response.status_code}: access denied."
                )

            response.raise_for_status()
            result = response.json()

            # Extract payload from A2A response envelope
            if "result" in result:
                a2a_result = result["result"]
                artifacts = a2a_result.get("artifacts", [])
                if artifacts:
                    logger.info(
                        "M3.achieved: A2A invocation successful, payload received for user %s",
                        user_id,
                    )
                    return {"artifacts": artifacts, "request_id": request_id}

            logger.warning(
                "M3.missed: A2A invocation returned no payload for user %s (attempt %d)",
                user_id,
                attempt + 1,
            )
            raise A2AClientError("External agent returned an empty payload.")

        except A2AAuthorizationError:
            raise  # Do not retry auth errors

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as exc:
            last_error = exc
            logger.warning(
                "A2A call attempt %d/%d failed for user %s: %s",
                attempt + 1,
                _MAX_RETRIES + 1,
                user_id,
                str(exc),
            )
            if attempt < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2 ** attempt)
                await asyncio.sleep(delay)

        except Exception as exc:  # noqa: BLE001
            last_error = exc
            logger.error(
                "Unexpected A2A error for user %s: %s",
                user_id,
                str(exc),
            )
            if attempt < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2 ** attempt)
                await asyncio.sleep(delay)

    logger.error(
        "M3.missed: A2A invocation failed after %d attempts for user %s",
        _MAX_RETRIES + 1,
        user_id,
    )
    raise A2AClientError(
        f"External document agent is temporarily unavailable after "
        f"{_MAX_RETRIES + 1} attempts. Please try again later. "
        f"Last error: {last_error}"
    )
