"""Multi-account selection and tenant_id switching for the GUI."""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal

from src.config import Config
from src.market.topstep_client import Account, TopstepClient
from src.runtime.tenancy import normalize_tenant_id

logger = logging.getLogger(__name__)


class AccountManager(QObject):
    """Manages multi-account selection and tenant_id switching.

    Lifecycle:
        1. Construct with the active Config.
        2. Call ``set_client()`` once the TopstepClient has authenticated.
        3. Call ``load_accounts()`` from a worker thread to populate the
           account list (emits ``accounts_loaded`` or ``account_error``).
        4. Call ``switch_account(account_id)`` when the operator selects a
           different account in the GUI dropdown.
    """

    account_changed = Signal(str)       # emits new account_id (str)
    accounts_loaded = Signal(list)      # emits list[Account]
    account_error = Signal(str)         # error message

    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        self._accounts: list[Account] = []
        self._active_account: Optional[Account] = None
        self._client: Optional[TopstepClient] = None

    # ------------------------------------------------------------------
    # Client binding
    # ------------------------------------------------------------------

    def set_client(self, client: TopstepClient) -> None:
        """Set the TopstepClient instance (must already be authenticated)."""
        self._client = client

    # ------------------------------------------------------------------
    # Account discovery
    # ------------------------------------------------------------------

    def load_accounts(self) -> None:
        """Fetch all tradable accounts from the TopstepX API.

        This performs a synchronous HTTP call and should be invoked from a
        background / worker thread.  On success the ``accounts_loaded``
        signal is emitted with a ``list[Account]``; on failure
        ``account_error`` is emitted with a human-readable message.
        """
        if self._client is None:
            self.account_error.emit("TopstepClient has not been set -- call set_client() first")
            return

        try:
            raw_accounts = self._client.list_accounts(only_active_accounts=True)
            if not raw_accounts:
                self.account_error.emit("No tradable accounts returned by the API")
                return

            parsed: list[Account] = []
            for raw in raw_accounts:
                parsed.append(self._client._account_summary(raw))

            self._accounts = parsed
            logger.info("Loaded %d tradable accounts", len(parsed))
            self.accounts_loaded.emit(list(parsed))

            # If no account is currently active, auto-select the first one
            # that matches the preferred_id_match pattern from config.
            if self._active_account is None:
                preferred = getattr(self._config.account, "preferred_id_match", "")
                auto_pick = None
                if preferred:
                    auto_pick = next(
                        (a for a in parsed if preferred.upper() in (a.name or "").upper()),
                        None,
                    )
                if auto_pick is None and parsed:
                    auto_pick = parsed[0]
                if auto_pick is not None:
                    self.switch_account(auto_pick.account_id)

        except Exception as exc:
            msg = f"Failed to load accounts: {exc}"
            logger.exception(msg)
            self.account_error.emit(msg)

    # ------------------------------------------------------------------
    # Account switching
    # ------------------------------------------------------------------

    def switch_account(self, account_id: str) -> None:
        """Switch the active account and update the global tenant_id.

        Parameters
        ----------
        account_id:
            The ``account_id`` string (as stored on :class:`Account`).
        """
        target = next(
            (a for a in self._accounts if str(a.account_id) == str(account_id)),
            None,
        )
        if target is None:
            self.account_error.emit(
                f"Account {account_id} not found in loaded accounts "
                f"({len(self._accounts)} available)"
            )
            return

        # Ask the broker client to make this the active account.
        if self._client is not None:
            selected = self._client.select_account(account_id)
            if selected is None:
                self.account_error.emit(
                    f"Broker rejected account selection for {account_id}"
                )
                return
            # Use the broker-returned object so balance/equity are fresh.
            target = selected

        self._active_account = target
        tenant_id = normalize_tenant_id(str(account_id))
        self._config.tenant_id = tenant_id

        logger.info(
            "Switched to account %s (%s) -- tenant_id=%s",
            target.account_id,
            target.name,
            tenant_id,
        )
        self.account_changed.emit(str(target.account_id))

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def active_account(self) -> Optional[Account]:
        """The currently selected :class:`Account`, or ``None``."""
        return self._active_account

    @property
    def accounts(self) -> list[Account]:
        """Snapshot of the last-loaded account list."""
        return list(self._accounts)
