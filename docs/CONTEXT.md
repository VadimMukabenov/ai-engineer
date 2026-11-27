# Продолжение AI Engineer

Дата: 2026-11-27 (Europe/Moscow). Репозиторий: `VadimMukabenov/ai-engineer`, **публичный по прямому указанию пользователя**. Это самостоятельный учебный проект; рабочие продукты/инфраструктура пользователя сюда не относятся.

## Цель и ограничения

Полностью удалённый AI Engineering, от $5000/month net, желаемо $10000+. РФ предпочтительна, Казахстан вторым вариантом. Английское интервью возможно; активная речь слабее пассивной. Заниматься готов полный день. Срок оффера не обещан.

Python основной стек. Все шесть capstone сохранены. Освоение: теория → упражнения → лабораторная → обратная связь → независимая проверка → проект → повторение. Полные принципы и ссылки в `docs/teaching-method.md`.

Ollama на loopback, официальный OpenAI Python SDK. Local-first smoke проверен: qwen2.5-coder:7b ответил OK, usage 36 prompt + 2 completion tokens, learner_evidence=false. Облачные вызовы не делались; платный бюджет $0. Будущий cloud требует явных provider/model/key/opt-in и согласованного бюджета; локальная совместимость не обещает API parity.

Не менять AmneziaWG/VPN, ядро, драйверы, системные пакеты или глобальный Beads. Обычный `bd` может вести в другой tracker; только `scripts/bd`. Отдельный prefix/database aie, CLI 1.0.3.

## Реализовано

- Learning Hub на FastAPI/Jinja, запускается `make serve`, адрес http://127.0.0.1:8765.
- Каталог: девять модулей, 45 навыков, 45 результатов, 30 записей занятий. Готовы D00/L00/LAB01/M00-THEORY; 26 planned. Шесть проектов пока имеют паспорта, приложения ещё не реализованы.
- Три отдельные области статуса: освоение, готовность demo, наблюдения рынка.
- Попытки переживают перезапуск; самостоятельность/версии/hash evidence проверяются. Тестовые записи живут во временных fixtures. Проверки не доказывают истинность ответа или личность автора.
- Контракт и snapshot каталога 1.0.0 под content-lock; версия и смысл критериев меняются по протоколу governance/README.md.
- 36 наблюдений вакансий: 33 verified / 3 partial, 530 строк матрицы. Это целевая выборка, не оценка долей стека. Нет подтверждённого одновременного salary+eligibility fit. См. research/market/review-notes.md.
- Beads отдельно, переносимый логический snapshot и проверка round-trip; оригинальные личные email не публикуются. Полная Dolt/audit history не переносится этим форматом.

## С чего продолжить обучение

Активная учебная задача: `aie-8ve`. Эпик основы `aie-qg3` повторно открыт: осталось завершить интеграцию PR1 после появления автоматической PR-проверки. Это не мешает учиться на платформе.

**Ответов на задания пока нет; один локальный самоотчёт D00; освоение 0/45.** Не писать ответы за пользователя. Текущий маршрут — M00-THEORY на платформе: объяснения → собственная запись после первого блока → разбор внутри платформы. К D00/независимым проверкам возвращаться после обучения по выявленным пробелам, без предварительной выдачи эталона. Подробно: `docs/assessment.md`.

26 занятий не считать написанными. Перед следующим этапом подготовить полный материал, упражнения, критерии и независимую задачу по утверждённым результатам; затем работать с учеником. Не сокращать шесть проектов до двух. Отклики начинаются при первом убедительном кейсе, без ожидания завершения всей программы.

## Перед любым изменением

1. Читать AGENTS.md, governance/plan.json и активную задачу `scripts/bd ready`.
2. `make verify`; `make status`; при изменении поведения `make test`.
3. Смотреть связанную часть каталога и критерии. Не объявлять готовность по одному pytest.
4. После работы сохранить факты и следующий шаг сюда и в Beads; создать свежий snapshot, проверить restore, отдельно проверить push.

## Ограничения и точная проверка

Текущие результаты проверки/сохранения: `governance/runtime-status.json` и `docs/verification.md`. GitHub CI и серверные права проверяются отдельно; файл AGENTS.md, lock и второй ИИ сами по себе не гарантируют отсутствие дрейфа. При недоступности tracker/CI нельзя подменять результат фиктивным успехом.

## Незавершённая интеграция

PR1 открыт. Задача `aie-ala`: automatic push/pull_request runs не появились, хотя ручные workflow_dispatch на main4f7fcb4 и branch63a3322 успешны. GitHub не засчитывает ручные workflow jobs как обязательный PR-check. Проверены Active workflow, enabled/all Actions, OAuth user, отсутствие skip в commit; изменение записи triggers на explicit mapping и quoted on не решило проблему. Root cause не установлен. Не подделывать status и не обходить protection. Основной код курса уже в main; финальные recovery-документы/скрипт/snapshots и эта диагностика сохранены в ветке PR1.

Полное remote restore branch63a3322 также прошло: 82 файла, 6 задач/6 deps, 0/45. Новый snapshot03 отражает 7 задач и повторно открытый эпик; его локальный round-trip прошёл. Последующие технические задачи не являются прогрессом ученика.

## Проект observability и управления моделью — 2026-11-27

По запросу пользователя подготовлены [спецификация](superpowers/specs/2026-11-27-observability-and-model-control-design.md), [полный каталог](observability/metric-catalog.md), машиночитаемый `docs/observability/metrics.json` и [независимое ревью](observability/design-review.md). 142 определения, семь приложений/профилей с тремя основными KPI каждый; это design-only proposal, сборщиков/значений/нового UI ещё нет. Канонические цели/критерии/content-lock и освоение не изменены.

Предлагается один контракт событий и корреляции с поэтапными runtime-профилями: bounded core → PostgreSQL analytics/ledger + OTel/Prometheus/Grafana → LiteLLM/Langfuse → полные trace/log/backup drills. Learning records остаются источником освоения; денежный ledger без sampling; trace IDs не Prometheus labels. Доказательства экспериментов immutable с manifest/hash; operational telemetry имеет TTL/квоты. Backup на том же SSD не выдавать за off-device backup; destination ещё не выбран. Сравнение A без LLM / B первый AI / C оптимизированный AI; cost savings B/C только при сопоставимых данных, полноте учёта и выполненных quality/safety guardrails. Никаких обещаний процентов до измерений.

Read-only preflight: Ollama active0.24.0, `/api/ps` пуст, qwen2.5-coder:7b установлен, GPU около1MiB/4096MiB. Раздел проекта заполнен98%, свободно около22GiB; не скачивать тяжёлые images/models и не чистить данные автоматически. Это снимок, не постоянный статус. Модельные load/unload/generate операции этой работой не выполнялись; VPN/ядро/драйверы/службы не менялись.

Проект тумблера «Локальный AI в учебной платформе» охватывает будущие встроенные generation/embedding вызовы Hub; отдельные CLI и capstone вне его gate. Загрузка/выгрузка — отдельные явные операции по Ollama API, systemd-сервис остаётся работать. Reviewer нашёл неоднозначность scope; исправлены scope и crash reconciliation. Для всех семи клиентов одновременно нужен центральный admission API, не общий JSON-флаг.

Следующий инженерный шаг: рассмотреть проект, затем составить отдельный implementation plan для core instrumentation и model status/control; не выдавать опубликованный draft за реализованную функцию. Учебный следующий шаг остаётся D00/aie-8ve, 0/45.

Проверки проекта: 142 уникальных metric IDs, семь валидных профилей, локальные Markdown-ссылки разрешаются; `make verify` valid=true; `make status` attempt_count=0/mastered=0/45; `git diff --check` без ошибок. Задача design `aie-8oq` закрыта по этому ограниченному результату. Новый public snapshot `backups/beads-2026-11-27-04` содержит восемь задач/шесть зависимостей; восстановление во временную изолированную БД verified=true. Работа ведётся в `codex/observability-design`, поверх ещё открытого PR1; для чистого review design diff база PR — `codex/course-foundation`. Автоматический CI blocker `aie-ala` этим документом не устранён.

Сохранение design подтверждено: GitHub PR2 https://github.com/VadimMukabenov/ai-engineer/pull/2 (draft, base codex/course-foundation). Полное восстановление из GitHub `python3 scripts/verify_restore.py --ref origin/codex/observability-design` на commit `f7c16beff257dc5a10c2cbeb0a14cc3ecc8637cb` прошло: valid=true, 90 tracked files, snapshot04, восемь задач/шесть зависимостей, IDs/статусы/export-поля/hash evidence/verify/status совпали, 0/45. Неудачный первый вызов с unqualified branch ref завершился до checkout; корректный remote-tracking ref проверен указанной командой. GitHub-коннектор вернул403 при создании PR; существующий gh создал PR2, attachment добавлен. Последующая дописка этого результата в CONTEXT — отдельный документальный commit, не новый прогон полного restore.

## Обучение внутри платформы — 2026-11-27

Уточнение пользователя: не проводить уроки в чате; всё обучение и прогресс — в Learning Hub. Правило добавлено в AGENTS.md/assessment.md. В чате только управление, краткий статус и ссылки. Нельзя снова задавать учебную задачу в чате вместо платформы.

Задача `aie-z7g`, ветка `codex/platform-learning-route` поверх опубликованного observability design. Подготовлен M00-THEORY: семь последовательных блоков, объяснения, собственные примеры, упражнения, официальные источники и форма для промежуточных ответов. Публикация предусмотренного урока: каталог1.0.1 со snapshot; старый1.0.0 сохранён. Следующий шаг M00-THEORY. Цели, состав модулей/результатов, criterion_version и шесть паспортов неизменны; M00-PRACTICE/CHECK остаются planned. Изменение и lock описаны в governance/changes/2026-11-27-platform-learning-route.md.

Самоотчёт о затруднении D00 сохранён дословно локально: kind=self_report, assistance=unspecified, recorded_by=mentor. Это не оценённые ответы и не подтверждённые0/9. Файл исключён через local .git/info/exclude, его текст не публикуется. В публичном clone этого личного файла не будет; отдельный off-device backup личных учебных записей пока не настроен. Не выдавать restore публичного кода за восстановление приватного самоотчёта.

В UI/API самоотчёты отделены от попыток ответа. Passed по самоотчёту отклоняется; неизвестная помощь не подтверждает самостоятельность. Старые JSON без полей kind/recorded_by читаются как answer/learner без перезаписи bytes/hash. Главная страница выводит реальный следующий урок и отдельный счётчик. Реальный перезапуск на8765 подтверждает:1 самоотчёт,0 ответов,0/45 mastery; история показывает происхождение записи.

Проверки: четыре новых regression tests сначала red, затем green; полный make test49passed. Есть один upstream StarletteDeprecationWarning об httpx/httpx2; runtime ошибки не обнаружены, зависимости не менялись. Ruff check passed; семь Python-примеров выполнены в существующем окружении без сети/моделей. make verify valid=true. CUA in-app browser: главная → «Открыть занятие» → M00-THEORY, содержимое/форма видны,0 console warn/error, screenshot537pxwide без обрезания текста. Исходная платформа остаётся http://127.0.0.1:8765.

Ближайший учебный шаг: открыть M00-THEORY на платформе, сохранить собственную запись после первого блока; наставник читает запись и размещает разбор/следующее упражнение в платформе. За ученика ничего не решено и не зачтено. Полноценный AI tutor и новая observability instrumentation этим блоком не реализованы.

Независимое code review по aie-z7g обнаружило P2: lookup отсутствующего next lesson вызывал StopIteration вместо отчёта integrity. Воспроизведено новым failing regression test; исправлено safe lookup + недоступный маршрут без сломанной ссылки в dashboard/history. Итоговый полный make test:50passed,1 upstream warning; make verify и ruff check passed. Публичный diff не содержит личный self_report; сохранение этой записи проверено локально после restart отдельно от public restore.

Свежий public Beads snapshot05: девять задач/шесть зависимостей/один комментарий; round-trip во временную изолированную БД verified=true. Сырые личные учебные записи в него не входят. Ветка для сохранения — codex/platform-learning-route; отдельный PR поверх codex/observability-design, без merge или обхода текущего CI blocker.

GitHub сохранение подтверждено: PR3 https://github.com/VadimMukabenov/ai-engineer/pull/3, base codex/observability-design. Remote restore commit2456abcdac039bf015a80b711b7d583e794c39ec: valid=true,96 tracked files, snapshot05, все сравнения кода/каталога/трекера/публичных records пройдены, next=M00-THEORY,0/45. Приватный самоотчёт намеренно не входит в публичный export и проверен отдельно локально. Последующая запись этого receipt в CONTEXT — отдельный документальный commit.
