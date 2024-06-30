from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class HeldAsset:
    """A dataclass that represents a financial asset held by the user."""

    account_number: str
    """The account number of the asset."""

    name: str
    """The name of the asset."""

    currency: str
    """The currency of the asset."""

    exchange_rate: float = field(repr=False)
    """The exchange rate of the currency."""

    market_value: float
    """The market value of the asset."""


@dataclass(frozen=True)
class HeldCash(HeldAsset):
    """A dataclass that represents cash held by the user."""


@dataclass(frozen=True)
class HeldCashEquivalent(HeldCash):
    """A dataclass that represents cash equivalents held by the user.

    Cash equivalents are liquid assets that are essentially interchangeable
    with cash and are generally held for a short period of time.
    """

    maturity_date: date
    """The date when the cash equivalent matures."""

    entry_value: float = field(repr=False)
    """The value of the cash equivalent when it was initially purchased or invested."""

    @property
    def pnl(self) -> float:
        """The profit or loss of the cash equivalent."""
        return self.market_value - self.entry_value

    @property
    def pnl_percent(self) -> float:
        """The profit or loss percentage of the cash equivalent."""
        return self.pnl / self.entry_value


@dataclass(frozen=True)
class HeldEquity(HeldAsset):
    """A dataclass that represents equity held by the user."""

    symbol: str
    """The symbol of the equity."""

    quantity: float
    """The quantity of the equity held."""

    entry_value: float = field(repr=False)
    """The value of the equity when it was initially purchased or invested."""

    @property
    def pnl(self) -> float:
        """The profit or loss of the equity."""
        return self.market_value - self.entry_value

    @property
    def pnl_percent(self) -> float:
        """The profit or loss percentage of the equity."""
        return self.pnl / self.entry_value

    @property
    def market_price(self) -> float:
        """The market price of the equity."""
        return self.market_value / self.quantity

    @property
    def entry_price(self) -> float:
        """The average price of the equity when it was initially purchased or invested."""
        return self.entry_value / self.quantity


@dataclass(frozen=True)
class HeldGoldSpot(HeldAsset):
    """A dataclass that represents gold spot held by the user."""

    symbol: str
    """The symbol of the gold spot."""

    quantity: float
    """The quantity of the gold spot held."""

    entry_value: float = field(repr=False)
    """The value of the gold spot when it was initially purchased or invested."""

    @property
    def pnl(self) -> float:
        """The profit or loss of the gold spot."""
        return self.market_value - self.entry_value

    @property
    def pnl_percent(self) -> float:
        """The profit or loss percentage of the gold spot."""
        return self.pnl / self.entry_value

    @property
    def market_price(self) -> float:
        """The market price of the gold spot."""
        return self.market_value / self.quantity

    @property
    def entry_price(self) -> float:
        """The average price of the gold spot when it was initially purchased or invested."""
        return self.entry_value / self.quantity


@dataclass(frozen=True)
class HoldingPeriodRecord:
    """A dataclass that represents an asset holding period record."""

    start_date: date
    """The start date of the holding period."""

    end_date: date
    """The end date of the holding period."""

    initial_value: int
    """The initial value of the asset."""

    closing_value: int
    """The closing value of the asset."""

    cash_inflow: int = field(repr=False)
    """The cash inflow of the asset during the holding period."""

    cash_outflow: int = field(repr=False)
    """ The cash outflow of the asset during the holding period."""

    @property
    def pnl(self) -> float:
        """The profit or loss of the asset during the holding period."""
        return self.closing_value - (self.initial_value + self.cash_inflow - self.cash_outflow)

    @property
    def pnl_percent(self) -> float:
        """The profit or loss percentage of the asset during the holding period."""
        return self.pnl / (self.initial_value + self.cash_inflow - self.cash_outflow)
