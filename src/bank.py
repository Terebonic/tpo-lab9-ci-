"""Бизнес-логика банковского счёта — объект модульного тестирования ЛР №6."""
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


class InsufficientFundsError(Exception):
    """Недостаточно средств на счёте."""


def to_money(value):
    """Привести сумму к Decimal с двумя знаками; допускаются int, str и Decimal (float — нет, из-за погрешности)."""
    if isinstance(value, bool) or not isinstance(value, (int, str, Decimal)):
        raise TypeError("Сумма должна быть int, str или Decimal")
    try:
        d = Decimal(value)
    except ArithmeticError:
        raise ValueError(f"Некорректная сумма: {value!r}") from None
    if not d.is_finite():
        raise ValueError(f"Некорректная сумма: {value!r}")
    return d.quantize(CENT, rounding=ROUND_HALF_UP)


class BankAccount:
    LOW_BALANCE = Decimal("100.00")

    def __init__(self, owner, balance=0, notifier=None):
        if not owner or not owner.strip():
            raise ValueError("Не указан владелец счёта")
        self.owner = owner.strip()
        self._balance = to_money(balance)
        if self._balance < 0:
            raise ValueError("Начальный баланс не может быть отрицательным")
        self.notifier = notifier
        self.history = []

    @property
    def balance(self):
        return self._balance

    def deposit(self, amount):
        amount = self._positive(amount)
        self._balance += amount
        self.history.append(("deposit", amount))
        return self._balance

    def withdraw(self, amount):
        amount = self._positive(amount)
        if amount > self._balance:
            raise InsufficientFundsError(f"Недостаточно средств: баланс {self._balance}, запрошено {amount}")
        self._balance -= amount
        self.history.append(("withdraw", amount))
        if self.notifier is not None and self._balance < self.LOW_BALANCE:
            self.notifier.notify(self.owner, f"Низкий баланс: {self._balance}")
        return self._balance

    def transfer(self, other, amount):
        if other is self:
            raise ValueError("Нельзя перевести деньги на тот же счёт")
        self.withdraw(amount)
        other.deposit(amount)
        return self._balance

    def apply_interest(self, rate_percent):
        """Начислить проценты (0–100 %), результат округляется до копеек."""
        rate = Decimal(str(rate_percent))
        if not Decimal(0) <= rate <= Decimal(100):
            raise ValueError("Ставка должна быть от 0 до 100 %")
        interest = (self._balance * rate / 100).quantize(CENT, rounding=ROUND_HALF_UP)
        self._balance += interest
        self.history.append(("interest", interest))
        return interest

    @staticmethod
    def _positive(amount):
        amount = to_money(amount)
        if amount <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        return amount


def is_valid_card(number):
    """Проверка номера карты по алгоритму Луна (13–19 цифр, пробелы допускаются)."""
    if not isinstance(number, str):
        raise TypeError("Номер карты передаётся строкой")
    digits = number.replace(" ", "")
    if not digits.isdigit() or not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0
