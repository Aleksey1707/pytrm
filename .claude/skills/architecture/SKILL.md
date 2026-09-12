---
name: architecture
description: "Свод архитектуры pytrm: слои пакета и граф импортов, публичный API в __init__.py и ре-экспорт через as, запрет impls в публичном API, единственный источник версии, неизменяемость контекста и владение им у ContextManager, Registry и однократная инициализация, configurate против get_configurated_reg, DI через create и keyword-only reg, контракт декораторов transactional и сентинел NOT_SET. Использовать при новом модуле в пакете, правке __init__.py, share.py, bases.py, configurations.py и decorators.py."
---

# 10-architecture.md

Прочитай `docs/rules/10-architecture.md` целиком перед правкой и следуй ему: свод обязателен,
пересказ по памяти не годится.

Осознанные отступления от сводов — `docs/rules/DEBT.md`. Сверься с ним, прежде чем
«чинить» найденное несоответствие: часть из них оставлена намеренно.
