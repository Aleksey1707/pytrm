---
name: propagation
description: "Свод распространения транзакции pytrm: семантика семи правил Propagation в таблице есть/нет транзакции, кортеж NON_TRANSACTIONAL_PROPAGATIONS, инварианты _initialize и _do, владение транзакцией кадром, который вызвал begin, запрет ручных commit и rollback, поведение exclude вплоть до BaseException и откат при отмене задачи, выбор правила через propagation и with_propagation, вложенные транзакции и NestedTransactionsNotSupportedTrmException. Использовать при правке bases.py, добавлении правила распространения и разборе поведения вложенных блоков do."
---

# 11-propagation.md

Прочитай `docs/rules/11-propagation.md` целиком перед правкой и следуй ему: свод обязателен,
пересказ по памяти не годится.

Осознанные отступления от сводов — `docs/rules/DEBT.md`. Сверься с ним, прежде чем
«чинить» найденное несоответствие: часть из них оставлена намеренно.
