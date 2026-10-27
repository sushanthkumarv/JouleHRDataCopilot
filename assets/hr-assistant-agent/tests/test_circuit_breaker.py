"""Tests for circuit_breaker module."""
import asyncio
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from circuit_breaker import CircuitBreaker


class TestCircuitBreakerInitialState:
    @pytest.mark.asyncio
    async def test_new_model_is_allowed(self):
        cb = CircuitBreaker()
        assert await cb.allows("model-a")

    @pytest.mark.asyncio
    async def test_unknown_model_is_allowed(self):
        cb = CircuitBreaker(failure_threshold=3)
        assert await cb.allows("unknown-model")


class TestCircuitBreakerSuccessReset:
    @pytest.mark.asyncio
    async def test_record_success_allows_model(self):
        cb = CircuitBreaker(failure_threshold=2)
        await cb.record_failure("model-a")
        await cb.record_success("model-a")
        assert await cb.allows("model-a")

    @pytest.mark.asyncio
    async def test_success_after_partial_failures_resets(self):
        cb = CircuitBreaker(failure_threshold=3)
        await cb.record_failure("model-a")
        await cb.record_success("model-a")
        # After success, failures should be reset
        await cb.record_failure("model-a")
        assert await cb.allows("model-a")  # threshold not reached yet


class TestCircuitBreakerOpening:
    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=10.0)
        await cb.record_failure("model-a")
        await cb.record_failure("model-a")
        # Now breaker should be open
        assert not await cb.allows("model-a")

    @pytest.mark.asyncio
    async def test_still_open_before_cooldown(self):
        cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=60.0)
        await cb.record_failure("model-a")
        assert not await cb.allows("model-a")


class TestCircuitBreakerHalfOpen:
    @pytest.mark.asyncio
    async def test_half_open_after_cooldown(self):
        # Use a mock time function
        now = [0.0]
        cb = CircuitBreaker(
            failure_threshold=1,
            cooldown_seconds=5.0,
            time_fn=lambda: now[0],
        )
        await cb.record_failure("model-a")
        # Advance time past cooldown
        now[0] = 6.0
        # Should now allow (half-open probe)
        assert await cb.allows("model-a")

    @pytest.mark.asyncio
    async def test_half_open_success_closes_breaker(self):
        now = [0.0]
        cb = CircuitBreaker(
            failure_threshold=1,
            cooldown_seconds=5.0,
            time_fn=lambda: now[0],
        )
        await cb.record_failure("model-a")
        now[0] = 6.0
        # Allow probe
        await cb.allows("model-a")
        # Probe succeeds
        await cb.record_success("model-a")
        # Should be fully closed
        assert await cb.allows("model-a")

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_breaker(self):
        now = [0.0]
        cb = CircuitBreaker(
            failure_threshold=1,
            cooldown_seconds=5.0,
            time_fn=lambda: now[0],
        )
        await cb.record_failure("model-a")
        now[0] = 6.0
        # Allow probe (transitions to half-open)
        await cb.allows("model-a")
        # Probe fails — re-opens
        await cb.record_failure("model-a")
        # Should be open again before another cooldown
        assert not await cb.allows("model-a")


class TestCircuitBreakerThresholdClamping:
    @pytest.mark.asyncio
    async def test_threshold_clamped_to_minimum_1(self):
        """Threshold below 1 is clamped to 1 to prevent immediate opening."""
        cb = CircuitBreaker(failure_threshold=0, cooldown_seconds=1.0)
        # Even with threshold=0, clamped to 1, so one failure opens
        await cb.record_failure("model-a")
        assert not await cb.allows("model-a")

    @pytest.mark.asyncio
    async def test_multiple_models_independent(self):
        cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=60.0)
        await cb.record_failure("model-a")
        # model-a is open, model-b is not
        assert not await cb.allows("model-a")
        assert await cb.allows("model-b")
