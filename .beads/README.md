# Beads этого курса

Использовать только `scripts/bd` из этого checkout. Обычный глобальный `bd` может быть подключён к другому рабочему tracker.

```bash
scripts/bd ready
scripts/bd list --json
scripts/bd show aie-qg3
```

Исходная локальная embedded база не входит в Git. Публичный логический snapshot сохраняется отдельно в `backups/`, с явным редактированием личных email. Его восстановление проверяется, но это не полный перенос Dolt/audit history. Правила, поддерживаемая версия CLI и команды: [docs/beads.md](../docs/beads.md).

Не утверждать, что push кода сохранил более поздние изменения tracker: сначала создать и проверить свежий snapshot, затем отдельно push.
