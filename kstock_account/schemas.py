from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class HeldAsset:
    account_number: str
    name: str
    currency: str
    exchange_rate: float = field(repr=False)
    market_value: float


@dataclass(frozen=True)
class HeldCash(HeldAsset):
    pass


@dataclass(frozen=True)
class HeldCashEquivalent(HeldCash):
    maturity_date: date
    entry_value: Optional[float] = field(repr=False)

    @property
    def pnl(self) -> float:
        return self.market_value - self.entry_value

    @property
    def pnl_percent(self) -> float:
        return self.pnl / self.entry_value

    @property
    def market_price(self) -> float:
        return self.market_value / self.quantity

    @property
    def entry_price(self) -> float:
        return self.entry_value / self.quantity


@dataclass(frozen=True)
class HeldEquity(HeldAsset):
    symbol: str
    quantity: float
    entry_value: Optional[float] = field(repr=False)

    @property
    def pnl(self) -> float:
        return self.market_value - self.entry_value

    @property
    def pnl_percent(self) -> float:
        return self.pnl / self.entry_value

    @property
    def market_price(self) -> float:
        return self.market_value / self.quantity

    @property
    def entry_price(self) -> float:
        return self.entry_value / self.quantity


@dataclass(frozen=True)
class HeldGoldSpot(HeldAsset):
    symbol: str
    quantity: float
    entry_value: Optional[float] = field(repr=False)

    @property
    def pnl(self) -> float:
        return self.market_value - self.entry_value

    @property
    def pnl_percent(self) -> float:
        return self.pnl / self.entry_value

    @property
    def market_price(self) -> float:
        return self.market_value / self.quantity

    @property
    def entry_price(self) -> float:
        return self.entry_value / self.quantity


@dataclass(frozen=True)
class HoldingPeriod:
    initial_value: int = field(repr=False)
    closing_value: int
    cash_inflow: int = field(repr=False)
    cash_outflow: int = field(repr=False)

    @property
    def pnl(self) -> float:
        return self.closing_value - (self.initial_value + self.cash_inflow - self.cash_outflow)

    @property
    def pnl_percent(self) -> float:
        return self.pnl / (self.initial_value + self.cash_inflow - self.cash_outflow)
