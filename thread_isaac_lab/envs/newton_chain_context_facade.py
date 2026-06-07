# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Dry-preflight facade for future chain-context evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

try:
    from chain_runtime_state import ChainRuntimeState
except ModuleNotFoundError:
    from .chain_runtime_state import ChainRuntimeState


@dataclass
class ChainRuntimeApiCheck:
    """Result of a dry chain-runtime API surface check."""

    skill_name: str
    ready: bool
    missing_methods: list[str] = field(default_factory=list)


class NewtonChainContextFacade:
    """Eval-only facade contract for a single shared Newton chain runtime.

    This Stage-0 implementation verifies that the required no-reset API exists.
    It deliberately refuses live stepping until a later GPU-authorized packet.
    """

    REQUIRED_ENV_METHODS = (
        "export_chain_state",
        "import_chain_state",
        "validate_chain_state",
        "step_chain",
        "get_observations",
    )

    def __init__(self, *, live_enabled: bool = False) -> None:
        """Initialize the dry facade.

        Args:
            live_enabled: Whether live env stepping is allowed. Stage-0 must
                leave this disabled.
        """

        self.live_enabled = live_enabled

    def verify_env_api(self, env: Any, *, skill_name: str) -> ChainRuntimeApiCheck:
        """Verify that an environment exposes the chain-runtime API surface."""

        missing = [name for name in self.REQUIRED_ENV_METHODS if not callable(getattr(env, name, None))]
        return ChainRuntimeApiCheck(skill_name=skill_name, ready=not missing, missing_methods=missing)

    def verify_state_schema(self, state: ChainRuntimeState) -> dict[str, Any]:
        """Return a compact state-schema summary for dry reports."""

        return state.summary()

    def assert_live_enabled(self) -> None:
        """Raise if a caller tries to use live stepping during Stage-0."""

        if not self.live_enabled:
            raise RuntimeError("NewtonChainContextFacade is Stage-0 dry-only; live stepping is not authorized.")

    def run_chain(self, *args: Any, **kwargs: Any) -> None:
        """Refuse live chain execution in Stage-0."""

        self.assert_live_enabled()
        raise NotImplementedError("Live chain execution requires a later Stage-1 packet.")
