"""
Halcyon Expanse — Economy System
Build Step 8: Two currencies (CompactScrip / LedgerMark) with floating exchange.
CS base 0.85 LM, fluctuation ±15%. Updated every 3600 ticks (1 hr game-time).
"""
import time
import random


class Economy:
    """Dual-currency economy with fluctuating exchange rates."""

    def __init__(self, rng=None, update_interval=3600.0):
        self.rng = rng or random.Random()
        self.update_interval = update_interval
        self.last_update = time.time()

        # Currency definitions
        self.currencies = {
            "CS": {"name": "CompactScrip", "symbol": "CS", "base_to_LM": 0.85, "fluctuation": 0.15},
            "LM": {"name": "LedgerMark", "symbol": "LM", "base_to_CS": 1.176, "fluctuation": 0.15},
        }

        # Current rates (CS per LM, LM per CS)
        self.rate_CS_to_LM = 0.85
        self.rate_LM_to_CS = 1.176

        # Player wallets
        self.wallets = {"CS": 100.0, "LM": 50.0}

        # Faction-controlled resource nodes (affects fluctuation direction)
        self.resource_nodes = {}

    def update_rates(self, force=False):
        """Update exchange rates based on time elapsed and faction control."""
        now = time.time()
        elapsed = now - self.last_update
        if not force and elapsed < self.update_interval:
            return False

        # Base fluctuation
        cs_fluct = self.rng.uniform(-0.15, 0.15)

        # Faction ownership bias: Ferro Compact control increases CS value
        ferro_nodes = sum(1 for v in self.resource_nodes.values() if v == "Ferro Compact")
        concord_nodes = sum(1 for v in self.resource_nodes.values() if v == "Concord Table")

        if ferro_nodes > concord_nodes:
            cs_fluct += 0.05  # Ferro control boosts CS
        elif concord_nodes > ferro_nodes:
            cs_fluct -= 0.03  # Concord stability slightly lowers CS

        self.rate_CS_to_LM = max(0.5, min(1.2, 0.85 + cs_fluct))
        self.rate_LM_to_CS = 1.0 / self.rate_CS_to_LM if self.rate_CS_to_LM > 0 else 1.176

        self.last_update = now
        return True

    def exchange(self, from_currency, to_currency, amount):
        """Exchange currency. Returns amount received or None if insufficient."""
        if from_currency not in self.wallets or to_currency not in self.wallets:
            return None
        if self.wallets[from_currency] < amount:
            return None

        if from_currency == "CS" and to_currency == "LM":
            received = amount * self.rate_CS_to_LM
        elif from_currency == "LM" and to_currency == "CS":
            received = amount * self.rate_LM_to_CS
        else:
            return None

        self.wallets[from_currency] -= amount
        self.wallets[to_currency] += received
        return received

    def get_balance(self, currency):
        return self.wallets.get(currency, 0.0)

    def add_funds(self, currency, amount):
        if currency in self.wallets:
            self.wallets[currency] += amount

    def claim_node(self, node_id, faction_name):
        self.resource_nodes[node_id] = faction_name

    def to_dict(self):
        return {
            "rates": {"CS_to_LM": self.rate_CS_to_LM, "LM_to_CS": self.rate_LM_to_CS},
            "wallets": self.wallets,
            "resource_nodes": self.resource_nodes,
            "last_update": self.last_update,
        }
