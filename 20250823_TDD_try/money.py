from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class Bank:
    rates: dict[Pair, float] = None

    def __post_init__(self):
        if self.rates is None:
            self.rates = {}
    
    def reduce(self, source: Expression, to: str) -> "Money":
        return source.reduce(self, to)

    def add_rate(self, from_currency: str, to_currency: str, rate: float) -> None:
        self.rates[Pair(from_currency, to_currency)] = rate

    def rate(self, from_currency: str, to_currency: str) -> float:
        if from_currency == to_currency:
            return 1
        rate = self.rates.get(Pair(from_currency, to_currency), None)
        if rate is None:
            raise ValueError(f"Rate not defined for {from_currency} to {to_currency}")
        return rate

@abstractmethod
@dataclass
class Expression:
    def reduce(self, bank: Bank, to: str) -> "Money":
        pass
    def plus(self, addend: Expression) -> "Expression":
        pass
    def times(self, multiplier: int) -> "Expression":
        pass


@dataclass
class Sum(Expression):
    augend: Expression
    addend: Expression

    def reduce(self, bank: Bank, to: str) -> "Money":
        amount = bank.reduce(self.augend, to).amount + bank.reduce(self.addend, to).amount
        return Money(amount, to)

    def plus(self, addend: Expression) -> "Sum":
        return Sum(self, addend)

    def times(self, multiplier: int) -> "Sum":
        return Sum(self.augend.times(multiplier), self.addend.times(multiplier))

@dataclass
class Pair:
    def __init__(self, from_currency: str, to_currency: str):
        self.from_currency = from_currency
        self.to_currency = to_currency

    def __eq__(self, other):
        if not isinstance(other, Pair):
            return NotImplemented
        return self.from_currency == other.from_currency and self.to_currency == other.to_currency
    
    def __hash__(self):
        return hash((self.from_currency, self.to_currency))


@dataclass
class Money:
    amount: float
    currency: str

    def __eq__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount
    
    def equals(self, other: "Money") -> bool:
        if self.currency is not other.currency:
            return False
        return self.amount == other.amount

    def times(self, multiplier: int) -> "Expression":
        return Money(self.amount * multiplier, self.currency)

    def plus(self, addend: "Expression") -> "Sum":
        return Sum(self, addend)

    def reduce(self, bank: Bank, to: str) -> "Expression":
        rate = bank.rate(self.currency, to)
        return Money(self.amount / rate, to)

    @staticmethod
    def dollar(amount: float) -> "Expression":
        return Money(amount, "USD")

    @staticmethod
    def franc(amount: float) -> "Expression":
        return Money(amount, "CHF")


