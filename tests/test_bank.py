"""Модульные тесты BankAccount на pytest: фикстуры, @pytest.mark.parametrize, pytest.raises, mock."""
from decimal import Decimal
from unittest.mock import Mock

import pytest

from src.bank import BankAccount, InsufficientFundsError, is_valid_card, to_money

D = Decimal


@pytest.fixture
def notifier():
    return Mock()


@pytest.fixture
def acc(notifier):
    return BankAccount("Матюшкин С.", 1000, notifier=notifier)


# ---------------- to_money ----------------
@pytest.mark.parametrize("value, expected", [
    (100, "100.00"), ("99.999", "100.00"), ("0.005", "0.01"), (D("12.3"), "12.30"), ("-5", "-5.00"),
])
def test_to_money(value, expected):
    assert to_money(value) == D(expected)


@pytest.mark.parametrize("value, exc", [
    (1.5, TypeError), (None, TypeError), (True, TypeError), ("abc", ValueError), ("NaN", ValueError),
    ("Infinity", ValueError),
])
def test_to_money_invalid(value, exc):
    with pytest.raises(exc):
        to_money(value)


# ---------------- создание ----------------
def test_create(acc):
    assert (acc.owner, acc.balance, acc.history) == ("Матюшкин С.", D("1000.00"), [])


@pytest.mark.parametrize("owner, balance, msg", [
    ("", 0, "владелец"), ("   ", 0, "владелец"), ("Иван", -1, "отрицательным"),
])
def test_create_invalid(owner, balance, msg):
    with pytest.raises(ValueError, match=msg):
        BankAccount(owner, balance)


# ---------------- пополнение / снятие ----------------
@pytest.mark.parametrize("amount, expected", [(1, "1001.00"), ("0.01", "1000.01"), ("250.50", "1250.50")])
def test_deposit(acc, amount, expected):
    assert acc.deposit(amount) == D(expected)


@pytest.mark.parametrize("amount", [0, -10, "-0.01"])
def test_deposit_not_positive(acc, amount):
    with pytest.raises(ValueError, match="больше нуля"):
        acc.deposit(amount)
    assert acc.balance == D("1000.00")


@pytest.mark.parametrize("amount, expected", [(400, "600.00"), (1000, "0.00"), ("999.99", "0.01")])
def test_withdraw(acc, amount, expected):
    assert acc.withdraw(amount) == D(expected)


def test_withdraw_insufficient(acc):
    with pytest.raises(InsufficientFundsError, match="Недостаточно средств"):
        acc.withdraw("1000.01")
    assert acc.balance == D("1000.00")


@pytest.mark.parametrize("amount, notified", [(899, False), (900, False), ("900.01", True), (1000, True)])
def test_low_balance_notification(acc, notifier, amount, notified):
    acc.withdraw(amount)
    assert notifier.notify.called is notified


def test_history(acc):
    acc.deposit(100)
    acc.withdraw(50)
    acc.apply_interest(10)
    assert acc.history == [("deposit", D("100.00")), ("withdraw", D("50.00")), ("interest", D("105.00"))]


# ---------------- перевод ----------------
def test_transfer(acc):
    other = BankAccount("Петров", 0)
    acc.transfer(other, 300)
    assert (acc.balance, other.balance) == (D("700.00"), D("300.00"))


def test_transfer_to_self(acc):
    with pytest.raises(ValueError, match="тот же счёт"):
        acc.transfer(acc, 10)


def test_transfer_insufficient_is_atomic(acc):
    other = BankAccount("Петров", 50)
    with pytest.raises(InsufficientFundsError):
        acc.transfer(other, 5000)
    assert (acc.balance, other.balance) == (D("1000.00"), D("50.00"))


# ---------------- проценты ----------------
@pytest.mark.parametrize("rate, expected", [(0, "0.00"), (7.5, "75.00"), (100, "1000.00"), ("0.333", "3.33")])
def test_interest(rate, expected):
    acc = BankAccount("Тест", 1000)
    assert acc.apply_interest(rate) == D(expected)
    assert acc.balance == D("1000.00") + D(expected)


@pytest.mark.parametrize("rate", [-0.1, 100.01])
def test_interest_out_of_range(acc, rate):
    with pytest.raises(ValueError, match="Ставка"):
        acc.apply_interest(rate)


# ---------------- алгоритм Луна ----------------
@pytest.mark.parametrize("number, valid", [
    ("4111 1111 1111 1111", True),      # Visa
    ("5555555555554444", True),         # Mastercard
    ("378282246310005", True),          # AmEx, 15 цифр
    ("2200000000000004", True),         # МИР
    ("4111 1111 1111 1112", False),     # неверная контрольная цифра
    ("411111111111", False),            # 12 цифр — меньше минимума
    ("41111111111111111111", False),    # 20 цифр — больше максимума
    ("4111-1111-1111-1111", False),     # недопустимые символы
    ("", False),
])
def test_is_valid_card(number, valid):
    assert is_valid_card(number) is valid


def test_is_valid_card_type():
    with pytest.raises(TypeError):
        is_valid_card(4111111111111111)
