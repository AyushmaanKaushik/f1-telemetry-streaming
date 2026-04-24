# Phase 0: Research & Architecture Decisions

## Binary Layout Optimization

- **Decision**: Improvise structural definitions mapped specifically to `models.py` rather than parsing exactly to the Codemasters C++ schema standard.
- **Rationale**: The official Codemasters F1 binary struct encompasses 22 distinct cars deeply nested. Since our Azure Medallion pipeline only demands the simplified variables we defined in Pydantic, enforcing a lightweight 1:1 struct payload for exactly these vars guarantees tests succeed without rewriting our parser to ignore hundreds of opponent variables.

## Struct Packing Formats

- **Packet 3 (Event)**: `4s` (4 bytes representing a 4-char string literal like 'SSTA', 'SEND').
- **Packet 7 (Car Status)**: `f f B B B` (11 bytes representing Fuel(float), ERS(float), Compound(int), Age(int), DRS(int)).
- **Packet 10 (Car Damage)**: `f f f f` (16 bytes representing FrontWing(float), RearWing(float), Engine(float), Tyre(float)).
