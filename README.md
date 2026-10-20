# ТПО, ЛР №9 — автотесты в CI/CD (GitHub Actions)

![Tests](https://github.com/Terebonic/tpo-lab9-ci/actions/workflows/tests.yml/badge.svg)

Матюшкин С. И., группа 231-331, «Тестирование программного обеспечения».

* `src/bank.py` — бизнес-логика банковского счёта (из ЛР №6);
* `tests/test_bank.py` — модульные тесты pytest (параметризация, mock);
* `tests/test_api.py` — тесты REST API DummyJSON (из ЛР №5), маркер `api`;
* `.github/workflows/tests.yml` — конвейер: flake8 → unit-тесты на Python 3.11/3.12/3.13 с покрытием ≥ 95 % → API-тесты.

Локальный запуск:

```bash
pip install -r requirements.txt
flake8 src tests
pytest -m "not api" --cov=src --cov-branch
pytest -m api
```
