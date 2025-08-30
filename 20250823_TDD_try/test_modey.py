from money import Money, Bank, Expression, Sum

class TestMoney():

    def test_dollar_multiplication(self) -> None:
        five_dollar = Money.dollar(5)
        assert five_dollar.times(2) == Money.dollar(10)
        assert five_dollar.times(3) == Money.dollar(15)

    def test_equals(self) -> None:
        five_dollars1 = Money.dollar(5)
        assert five_dollars1.equals(Money.dollar(5))
        assert not five_dollars1.equals(Money.dollar(6))
        assert 5 == five_dollars1.amount
        five_franc1 = Money.franc(5)
        assert five_franc1.equals(Money.franc(5))
        assert not five_franc1.equals(Money.franc(6))
        assert 5 == five_franc1.amount
        # dollarとfrancは同じamountでも等しくない
        assert not five_dollars1.equals(five_franc1)
        assert not five_franc1.equals(five_dollars1)

    def test_franc_multiplication(self) -> None:
        five_franc = Money.franc(5)
        assert five_franc.times(2) == Money.franc(10)
        assert five_franc.times(3) == Money.franc(15)

    def test_currency(self) -> None:
        assert "USD" == Money.dollar(1).currency
        assert "CHF" == Money.franc(1).currency

    # def test_different_currency_class_equality(self) -> None:
    #     assert Money(10, "USD").equals(Dollar(10, "USD"))

    def test_simple_addition(self) -> None:
        five_dollars = Money.dollar(5)
        sum = five_dollars.plus(Money.dollar(5))
        bank = Bank()
        # assert sum == Money.dollar(10)
        reduced = bank.reduce(sum, "USD")
        assert reduced == Money.dollar(10)

    def test_plus_returns_sum(self) -> None:
        five_dollars = Money.dollar(5)
        sum = five_dollars.plus(Money.dollar(5))
        assert five_dollars == sum.augend
        assert Money.dollar(5) == sum.addend

    def test_reduce_sum(self) -> None:
        sum :Expression = Sum(Money.dollar(3), Money.dollar(4))
        bank = Bank()
        result = bank.reduce(sum, "USD")
        assert result == Money.dollar(7)

    def test_reduce_money(self) -> None:
        bank = Bank()
        result = bank.reduce(Money.dollar(1), "USD")
        assert result == Money.dollar(1)

    def test_reduce_money_different_currency(self) -> None:
        bank = Bank()
        bank.add_rate("CHF", "USD", 2)
        result = bank.reduce(Money.franc(2), "USD")
        assert result == Money.dollar(1)

    def test_identity_rate(self) -> None:
        bank = Bank()
        assert bank.rate("USD", "USD") == 1

    def test_mixed_addition(self) -> None:
        five_dollars = Money.dollar(5)
        ten_francs = Money.franc(10)
        bank = Bank()
        bank.add_rate("CHF", "USD", 2)
        result = bank.reduce(five_dollars.plus(ten_francs), "USD")
        assert result == Money.dollar(10)

    def test_sum_plus_money(self) -> None:
        five_dollars = Money.dollar(5)
        ten_francs = Money.franc(10)
        bank = Bank()
        bank.add_rate("CHF", "USD", 2)
        sum = Sum(five_dollars, ten_francs).times(2)
        result = bank.reduce(sum, "USD")
        assert result == Money.dollar(20)

    def test_sum_times(self) -> None:
        five_dollars = Money.dollar(5)
        ten_francs = Money.franc(10)
        bank = Bank()
        bank.add_rate("CHF", "USD", 2)
        sum = Sum(five_dollars, ten_francs).plus(five_dollars)
        result = bank.reduce(sum.times(2), "USD")
        assert result == Money.dollar(30)

    # def test_plus_same_currency_returns_money(self) -> None:
    #     sum = Money.dollar(1).plus(Money.dollar(1))
    #     assert isinstance(sum, Money)
    #     assert sum.equals(Money.dollar(2))