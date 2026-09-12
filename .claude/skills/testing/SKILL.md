---
name: testing
description: "Свод тестов pytrm: фикстуры conftest (context, settings, registry, init_default_registry) и шов transaction_manager в conftest реализации, общие наборы shared_test_propagation и ре-экспорт через as, маркер integration и testcontainers с session-областью, разделение test-fast и tox, разметка # given/when/then, pytest.raises вместо try/except, требования к покрытию публичного API и всех семи правил распространения. Использовать при новом тесте, правке тестовой обвязки и добавлении набора для новой реализации."
---

# 19-testing.md

Прочитай `docs/rules/19-testing.md` целиком перед правкой и следуй ему: свод обязателен,
пересказ по памяти не годится.

Осознанные отступления от сводов — `docs/rules/DEBT.md`. Сверься с ним, прежде чем
«чинить» найденное несоответствие: часть из них оставлена намеренно.
