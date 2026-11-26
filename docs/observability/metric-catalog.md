# Каталог метрик · проект 0.1.0

Всего 142 определений. Это проект измерений: сбор данных ещё не реализован, фактических значений здесь нет. Сначала показываем три основных показателя и ограничения каждого приложения; остальные доступны для диагностики.

Машиночитаемый источник: [metrics.json](metrics.json). Общие условия измерений и архитектура — в [проектном документе](../superpowers/specs/2026-11-27-observability-and-model-control-design.md).

Нулевой знаменатель — N/A; неизвестная стоимость/usage — unknown. Направление context означает, что больше или меньше само по себе не лучше. Условия и рамки каждого теста обязательны.

## Общие метрики всех AI-сервисов

| ID | Показатель / единица | Определение | Источник |
|---|---|---|---|
| `common.task_success_rate` | Успешные предметные задачи · ratio | Число задач, прошедших заранее заданную предметную рубрику, / все назначенные eligible cases закреплённого workload, включая admission rejections, ошибки и таймауты. Online accepted-only cohort показывать отдельно, не подменять им benchmark. | `task_events + evaluations` |
| `common.api_cost_per_success_usd` | Расход API на успешную задачу · USD/task | Сумма стоимости всех upstream-попыток прогона, включая неудачные/повторы/fallback/embeddings, / число успешных задач. При неполном учёте значение incomplete, не полная стоимость. | `provider_attempts + evaluations` |
| `common.successful_tasks_per_minute` | Полезная пропускная способность · task/min | Число завершённых предметно успешных задач / wall-clock минуты измерительного окна; очередь и завершение учитываются по одному правилу, отдельно от arrival rate. | `task_events + evaluations` |
| `common.latency_p50_seconds` | Полная задержка p50 · s | Медиана monotonic(end-start) по всем terminal задачам; timeout/cancellation помечаются, а не исчезают из отчёта. | `task_events` |
| `common.latency_p95_seconds` | Полная задержка p95 · s | 95-й перцентиль end-to-end длительности terminal задач, включая очередь; сообщать N и цензурирование timeout, не усреднять перцентили. | `task_events` |
| `common.stream_ttft_seconds` | До первого содержательного токена · s | Monotonic(first_content-start) для streaming; запросы без токена показываются отдельно как failures, не как нулевой TTFT. | `provider_attempts` |
| `common.queue_wait_seconds` | Ожидание в очереди · s | Monotonic(worker_started-accepted), p50/p95; rejected-before-queue учитываются отдельно. | `task_events` |
| `common.error_rate` | Технические ошибки · ratio | Ошибки/таймауты/разрывы соединения / все допущенные задачи; предметный корректный отказ не техническая ошибка. | `task_events` |
| `common.cancellation_rate` | Отмены · ratio | Отменённые задачи / все допущенные задачи с указанием initiator и стадии. | `task_events` |
| `common.rejection_rate` | Отказы admission/backpressure · ratio | Отклонённые до исполнения входы / все входы; причины disabled/budget/overload различаются. | `task_events` |
| `common.provider_attempts_per_task` | Вызовы провайдера на задачу · attempt/task | Все upstream attempts / число задач; один пользовательский запрос может иметь несколько попыток. | `provider_attempts` |
| `common.retry_rate` | Повторные upstream-попытки · ratio | Попытки с attempt_no>1 и reason=retry / все upstream attempts; fallback отдельно. | `provider_attempts` |
| `common.fallback_task_rate` | Задачи с fallback · ratio | Задачи с хотя бы одним fallback / задачи, дошедшие до маршрутизации. | `provider_attempts` |
| `common.cache_hit_rate` | Попадания в прикладной кэш · ratio | Ответы из валидного version-aware cache / lookup кэшируемых задач; не смешивать с provider prompt caching. | `task_events` |
| `common.stale_cache_rate` | Устаревшие ответы кэша · ratio | Проверенные cache-hit ответы с неверной версией источника/политики / все проверенные cache hits. | `evaluations` |
| `common.input_uncached_tokens` | Некэшированные входные токены · token | Сумма provider-reported uncached input в нормализованной схеме; cached input является частью total input и не суммируется повторно. | `provider_attempts` |
| `common.input_cached_tokens` | Кэшированные входные токены · token | Сумма provider-reported cached input; unknown остаётся null, не нулём. | `provider_attempts` |
| `common.output_tokens` | Выходные токены · token | Сумма reported output; reasoning может быть подмножеством output, следовать версии usage-mapping. | `provider_attempts` |
| `common.output_tokens_per_second` | Скорость decode · token/s | output eval_count / eval_duration seconds у Ollama, отдельно от prefill/load/end-to-end; не среднее от несопоставимых engines. | `provider_attempts` |
| `common.usage_coverage` | Полнота учёта usage · ratio | Upstream attempts с валидным usage / все billable attempts, включая errored; неизвестные поля показываются отдельно. | `provider_attempts` |
| `common.cost_coverage` | Полнота оценки расхода · ratio | Billable attempts с известной стоимостью и basis / все billable attempts; неполный числитель расхода не выдавать за полный. | `provider_attempts` |
| `common.cost_reconciliation_delta_usd` | Расхождение с расчётами провайдера · USD | Сопоставленная сумма ledger минус независимый invoice/usage export за те же период, аккаунт, валюту и scope; до доступа unknown. | `cost_reconciliations` |
| `common.schema_valid_rate` | Соответствие выходной схеме · ratio | Валидные по версии Pydantic-схемы ответы / ответы, от которых требуется структурированный результат; не доказывает предметную истинность. | `evaluations` |
| `common.retrieval_recall_at_k` | Retrieval Recall@k · ratio | Для каждого размеченного вопроса найденные релевантные документы в top-k / все релевантные; macro-average только по релевантно размеченным вопросам. | `evaluations` |
| `common.retrieval_ndcg_at_k` | Ранжирование nDCG@k · score | DCG@k / IDCG@k по закреплённым relevance labels, затем macro-average; k и gain-function версионированы. | `evaluations` |
| `common.citation_precision` | Точность ссылок · ratio | Цитаты, поддерживающие соответствующее утверждение и правильную версию документа, / все проверенные цитаты. | `evaluations` |
| `common.unsupported_claim_rate` | Неподтверждённые утверждения · ratio | Проверяемые фактические утверждения без допустимого подтверждения / все проверяемые фактические утверждения; рубрика явная. | `evaluations` |
| `common.tool_action_success_rate` | Корректность инструментальных действий · ratio | Правильные авторизованные эффекты или корректные предметные отказы / размеченные tool-action сценарии; HTTP200 не критерий. | `tool_audit + evaluations` |
| `common.unauthorized_effect_count` | Недопустимые эффекты · count | Число реально записанных запрещённых sandbox-эффектов в policy/adversarial сценариях; попытки и исполнение считать отдельно. | `tool_audit` |
| `common.cross_tenant_leak_count` | Межтенантная утечка · count | Число сценариев, где ответ/инструмент/трасса раскрыли данные чужого synthetic tenant, / дополнительно N проверенных атак. | `evaluations + tool_audit` |
| `common.human_review_rate` | Задачи с вмешательством · ratio | Задачи, потребовавшие человеческой проверки, / все задачи; обязательное HITL не считать дефектом или целью устранить. | `review_events` |
| `common.human_active_review_seconds` | Активное время человека · s/task | Наблюдаемое активное время проверки/исправления на задачу по одной методике; wall-clock ожидание модели и самооценку хранить отдельно. | `review_events` |
| `common.instrumentation_overhead_ratio` | Накладные расходы телеметрии · ratio | Парная разница p95 с/без telemetry / p95 без telemetry на том же workload; отдельный эксперимент, не выключать telemetry только у оптимизированной версии. | `experiment_results` |

## Учебная платформа

Основные: `learning-hub.independent_transfer_pass_rate`, `learning-hub.spaced_retrieval_pass_rate`, `learning-hub.tutor_cost_per_verified_help_usd`.

Ограничения: `learning-hub.false_mastery_award_count`, `learning-hub.attempt_persistence_failure_count`.

| ID | Показатель / единица | Определение | Источник |
|---|---|---|---|
| `learning-hub.mastered_outcome_ratio` | Освоенные результаты · ratio | Уникальные подтверждённые результаты действующей версии / все активные результаты версии; старые достижения и помощь не теряются. | `learner_records` |
| `learning-hub.independent_transfer_pass_rate` | Самостоятельный перенос · ratio | Первые независимые transfer-попытки, прошедшие рубрику, / все назначенные и начатые первые transfer-попытки; просроченные неначатые показывать отдельно. | `learner_records` |
| `learning-hub.spaced_retrieval_pass_rate` | Сохранение знаний · ratio | Успешные проверки повторения / выполненные due-проверки в закреплённом окне; рядом due coverage, иначе результат смещается пропусками. | `learner_records` |
| `learning-hub.spaced_retrieval_coverage` | Охват повторения · ratio | Выполненные due-проверки / все due-проверки по schedule version за окно; пересмотр расписания не переписывает историю. | `learner_records` |
| `learning-hub.first_attempt_pass_rate` | Первая самостоятельная попытка · ratio | Первые попытки с assistance none/documentation, прошедшие критерий, / все первые независимые попытки; анализировать по теме/сложности. | `learner_records` |
| `learning-hub.remediation_recheck_pass_rate` | Результат разбора пробела · ratio | Новые независимые проверки после remediation, прошедшие критерий, / выполненные rechecks; describe within-person change, не причинный эффект курса. | `learner_records` |
| `learning-hub.assistance_distribution` | Происхождение решений · distribution | Количество попыток по none/documentation/hint/ai_partial/ai_solution; не сводить помощь к баллу компетентности. | `learner_records` |
| `learning-hub.active_learning_minutes` | Время самостоятельной практики · min | Помеченное пользователем/наблюдаемое активное время с методом и idle-policy; открытая вкладка не означает обучение. | `learner_records + activity_events` |
| `learning-hub.review_turnaround_seconds` | Ожидание проверки · s | Время от сохранения попытки до первой содержательной оценки; API round-trip не заменяет это время. | `learner_records` |
| `learning-hub.assessment_evidence_valid_rate` | Целостность оценок · ratio | Оценки с существующими неизменёнными attempt/evidence и валидной версией / все оценки; искусственный success не создавать. | `integrity_checks` |
| `learning-hub.false_mastery_award_count` | Ошибочные зачёты · count | Контрольные сценарии, где помощник/невалидное evidence/чужая версия получили mastery; только проверяемые acceptance fixtures. | `integrity_checks` |
| `learning-hub.attempt_persistence_failure_count` | Потерянные попытки · count | Подтверждённые клиенту durable save, отсутствующие/повреждённые после restart/recovery; отдельно N контрольных сохранений. | `integrity_checks` |
| `learning-hub.ready_demo_count` | Демонстрируемые проекты · count | Проекты с воспроизводимой отдельной demo, выполненными критериями и evidence / рядом обязательное число6; паспорт planned не demo. | `demo_verifications` |
| `learning-hub.market_evidence_coverage` | Подтверждённые требования выбранных ролей · ratio | Требования из явно выбранного verified role cohort с проверенным mapping и достаточным evidence / все выбранные применимые требования; mapping/частичные/eligibility unknown отдельно. | `market_snapshots + evidence_mappings` |
| `learning-hub.tutor_helpful_verified_rate` | Проверенная полезность наставника · ratio | Ответы наставника, признанные корректными и полезными по рубрике независимой проверки, / проверенные ответы; положительный feedback ученика отдельно. | `tutor_evaluations` |
| `learning-hub.tutor_cost_per_verified_help_usd` | Цена полезного ответа наставника · USD/answer | Все API-затраты tutor-когорты / проверенно полезные ответы той же когорты; пока tutor отсутствует not_applicable. | `provider_attempts + tutor_evaluations` |
| `learning-hub.tutor_solution_leak_rate` | Разглашение решения проверки · ratio | Контрольные prompts, где наставник преждевременно выдал закрытый ответ независимой проверки, / все такие adversarial prompts. | `tutor_evaluations` |
| `learning-hub.practice_session_resume_success_rate` | Восстановление учебного контекста · ratio | Сценарии нового чата/restart с правильной версией, последней попыткой и следующим шагом / все контрольные resume-сценарии. | `recovery_drills` |
| `learning-hub.backup_age_seconds` | Возраст проверенной копии · s | Now минус created_at последней копии, прошедшей restore; наличие файла без проверки не означает verified backup. | `backup_runs` |
| `learning-hub.recovery_drill_seconds` | Время восстановления стенда · s | Monotonic от старта clean restore до integrity/status checks pass; указывать состав данных и объём, не обещать production RTO. | `recovery_drills` |

## Поддержка и возвраты

Основные: `support-agent.correct_resolution_rate`, `common.api_cost_per_success_usd`, `support-agent.human_active_seconds`.

Ограничения: `support-agent.unapproved_refund_count`, `support-agent.duplicate_refund_effect_count`.

| ID | Показатель / единица | Определение | Источник |
|---|---|---|---|
| `support-agent.correct_resolution_rate` | Корректное разрешение обращения · ratio | Сценарии с ожидаемыми ответом, политикой, эскалацией и sandbox-эффектом / все размеченные обращения; правильный отказ тоже может быть успехом. | `evaluations + tool_audit` |
| `support-agent.human_active_seconds` | Активное время оператора · s/ticket | Время проверки/действий оператора на обращение в парном учебном исследовании; ожидание и активность различаются. | `review_events` |
| `support-agent.eligible_auto_resolution_rate` | Автоматизация допустимых обращений · ratio | Корректно решённые без необязательного вмешательства обращения / заранее определённые eligible обращения; обязательное согласование возврата остаётся. | `evaluations + review_events` |
| `support-agent.policy_decision_accuracy` | Соблюдение политики возврата · ratio | Правильные allow/deny/escalate решения / все размеченные решения по закреплённой версии политики. | `evaluations` |
| `support-agent.refund_amount_error_minor_units` | Ошибка суммы возврата · minor_currency_unit | Абсолютное отклонение записанной sandbox суммы от ожидаемой; валюты не смешивать. | `tool_audit + evaluations` |
| `support-agent.duplicate_refund_effect_count` | Повторные финансовые эффекты · count | Дополнительные sandbox возвраты для одного idempotency scope при повторе/сбое/restart. | `tool_audit` |
| `support-agent.unapproved_refund_count` | Возвраты без одобрения · count | Записанные эффекты без действительного разрешения человека/прав/лимита на момент исполнения. | `tool_audit` |
| `support-agent.human_override_rate` | Исправления решения оператором · ratio | Изменённые человеком substantive решения / все проверенные решения; классифицировать ошибку и предпочтение. | `review_events` |
| `support-agent.checkpoint_resume_success_rate` | Продолжение после HITL/restart · ratio | Успешные восстановленные сценарии без двойного эффекта / все fault-injection resume-сценарии. | `recovery_drills` |
| `support-agent.policy_version_error_rate` | Устаревшая политика · ratio | Решения с неверной для сценария версией политики / все version-change сценарии. | `evaluations` |

## Аналитик инцидентов

Основные: `incident-analyst.report_correct_rate`, `common.api_cost_per_success_usd`, `incident-analyst.active_triage_seconds`.

Ограничения: `incident-analyst.false_causal_claim_rate`, `incident-analyst.remedial_effect_count`.

| ID | Показатель / единица | Определение | Источник |
|---|---|---|---|
| `incident-analyst.report_correct_rate` | Корректный разбор инцидента · ratio | Разборы, прошедшие рубрику timeline/evidence/гипотез/неопределённости, / все synthetic incidents, включая missing-data случаи. | `evaluations` |
| `incident-analyst.active_triage_seconds` | Активное время до приемлемой гипотезы · s/incident | Время человека до первой обоснованной гипотезы в сценарном drill; это не production MTTR. | `review_events` |
| `incident-analyst.root_cause_hit_at_3` | Причина в трёх гипотезах · ratio | Answerable инциденты с ground-truth причиной в top3 / все answerable инциденты; отсутствие ответа считается miss, unanswerable отдельно. | `evaluations` |
| `incident-analyst.timeline_event_precision` | Точность timeline · ratio | Правильно привязанные релевантные события / события выданного timeline. | `evaluations` |
| `incident-analyst.timeline_event_recall` | Полнота timeline · ratio | Выданные релевантные события / все размеченные существенные события инцидента. | `evaluations` |
| `incident-analyst.temporal_order_accuracy` | Порядок событий · ratio | Корректно упорядоченные сравнимые пары событий / размеченные сравнимые пары; неопределённые времена не придумывать. | `evaluations` |
| `incident-analyst.false_causal_claim_rate` | Ложные причинные выводы · ratio | Неподдержанные причинные утверждения / все проверенные причинные утверждения; не путать с простым correlation. | `evaluations` |
| `incident-analyst.unknown_handling_accuracy` | Работа с недостающими данными · ratio | Верные abstain/uncertainty/next-check ответы / размеченные unanswerable/partial incidents. | `evaluations` |
| `incident-analyst.source_locator_accuracy` | Верные ссылки на события · ratio | Точные ссылки на неизменяемый log event/version / проверенные ссылки. | `evaluations` |
| `incident-analyst.remedial_effect_count` | Самовольное исправление сервисов · count | Фактические remedial side effects; в этом проекте разрешена диагностика, не управление рабочими сервисами. | `tool_audit` |

## Аудитор договоров

Основные: `contract-auditor.critical_risk_recall`, `common.api_cost_per_success_usd`, `contract-auditor.active_review_seconds`.

Ограничения: `contract-auditor.risk_precision`, `contract-auditor.stale_document_reference_count`.

| ID | Показатель / единица | Определение | Источник |
|---|---|---|---|
| `contract-auditor.critical_risk_recall` | Полнота критических учебных рисков · ratio | Найденные размеченные critical risks / все размеченные critical risks; severity policy задана до теста, legal verdict не автоматизируется. | `evaluations` |
| `contract-auditor.active_review_seconds` | Активное время проверки договора · s/document | Наблюдаемое активное время человека на проверку одинаковых policy cases; после однократного знакомства использовать counterbalanced порядок. | `review_events` |
| `contract-auditor.risk_precision` | Точность риск-флагов · ratio | Подтверждённые policy risk flags / все выданные flags, по уровням severity. | `evaluations` |
| `contract-auditor.clause_extraction_f1` | Извлечение положений · score | Micro F1 извлечённых typed clauses против разметки по document/locator/value; matching rule версионирован. | `evaluations` |
| `contract-auditor.cross_reference_accuracy` | Перекрёстные ссылки · ratio | Верно разрешённые/верно признанные отсутствующими ссылки / размеченные ссылки. | `evaluations` |
| `contract-auditor.citation_version_accuracy` | Цитата и версия договора · ratio | Флаги с точной supporting цитатой, locator и версией / все проверенные флаги. | `evaluations` |
| `contract-auditor.missing_vs_conflicting_accuracy` | Отсутствие против противоречия · ratio | Верная классификация absent/conflicting/present / случаи соответствующей рубрики. | `evaluations` |
| `contract-auditor.unsupported_risk_rate` | Необоснованные риски · ratio | Флаги без правила или подтверждения документом / все выданные флаги. | `evaluations` |
| `contract-auditor.stale_document_reference_count` | Ссылки на старую редакцию · count | Флаги, опирающиеся на недопустимую предыдущую редакцию в version-change test. | `evaluations` |
| `contract-auditor.ocr_parse_field_error_rate` | Ошибки OCR/парсинга · ratio | Неверно извлечённые контрольные поля / размеченные поля до генерации; указывать тип файла, не маскировать LLM результатом. | `parser_evaluations` |

## Безопасный Text-to-SQL

Основные: `text-to-sql.execution_result_accuracy`, `common.api_cost_per_success_usd`, `common.successful_tasks_per_minute`.

Ограничения: `text-to-sql.unsafe_statement_executed_count`, `text-to-sql.cross_tenant_result_count`.

| ID | Показатель / единица | Определение | Источник |
|---|---|---|---|
| `text-to-sql.execution_result_accuracy` | Верный результат SQL · ratio | Answerable вопросы с правильным набором/агрегатом по oracle SQL и rubric / все answerable вопросы, включая ошибки и отказы; SQL-текст не должен совпадать дословно. | `evaluations + query_audit` |
| `text-to-sql.question_coverage` | Покрытие вопросов · ratio | Вопросы, на которые дан допустимый проверенный ответ / весь закреплённый workload; отдельно корректные отказы и clarifications. | `evaluations` |
| `text-to-sql.semantic_definition_accuracy` | Верные метрика и период · ratio | Ответы с правильной semantic definition, фильтрами и временными границами / размеченные вопросы. | `evaluations` |
| `text-to-sql.clarification_precision` | Уместность уточнения · ratio | Необходимые корректные уточнения / все запросы на уточнение; сообщать также recall. | `evaluations` |
| `text-to-sql.clarification_recall` | Обнаружение неоднозначности · ratio | Неоднозначные случаи с нужным уточнением до выполнения / все размеченные неоднозначные случаи. | `evaluations` |
| `text-to-sql.unsafe_statement_executed_count` | Исполненный запрещённый SQL · count | DDL/DML/многооператорные/запрещённые функции, фактически выполненные вопреки политике; attempted отдельно. | `query_audit` |
| `text-to-sql.cross_tenant_result_count` | Чужие строки в результате · count | Случаи выдачи/чтения недопустимого tenant через любые query/result paths в тестах. | `query_audit + evaluations` |
| `text-to-sql.query_timeout_rate` | Таймаут SQL · ratio | Запросы, прерванные statement timeout, / все фактически запущенные запросы. | `query_audit` |
| `text-to-sql.query_execution_seconds` | Исполнение в PostgreSQL · s/query | Время собственно DB execution отдельно от очереди, LLM generation и ответа; p50/p95. | `query_audit` |
| `text-to-sql.query_buffer_reads` | Работа чтения БД · block/query | Измеренные buffer reads на безопасном sandbox workload по согласованному методу; не выдавать planned EXPLAIN estimate за actual reads. | `query_measurements` |
| `text-to-sql.join_fanout_error_rate` | Ошибки кратности join · ratio | Неверные результаты на размеченных fan-out случаях / все такие случаи. | `evaluations` |

## Помощник рекрутера

Основные: `recruitment-assistant.fact_extraction_micro_f1`, `common.api_cost_per_success_usd`, `recruitment-assistant.active_review_seconds`.

Ограничения: `recruitment-assistant.unsupported_experience_count`, `recruitment-assistant.unapproved_hiring_decision_count`.

| ID | Показатель / единица | Определение | Источник |
|---|---|---|---|
| `recruitment-assistant.fact_extraction_micro_f1` | Точность извлечения фактов · score | Micro F1 typed фактов против synthetic annotations с точными provenance; не рейтинг/решение о людях. | `evaluations` |
| `recruitment-assistant.active_review_seconds` | Активное время проверки резюме · s/document | Время человека на сверку фактов и оснований по синтетическим документам; не время до найма. | `review_events` |
| `recruitment-assistant.requirement_evidence_accuracy` | Сопоставление требования и evidence · ratio | Верные confirmed/contradictory/unknown основания / все размеченные requirement-document пары. | `evaluations` |
| `recruitment-assistant.contradiction_f1` | Выявление противоречий · score | F1 размеченных конфликтов дат/источников/сведений; precision и recall сохраняются рядом. | `evaluations` |
| `recruitment-assistant.unknown_handling_accuracy` | Сохранение unknown · ratio | Верно оставленные unknown / случаи отсутствующей информации; false unknown на известных фактах отдельно. | `evaluations` |
| `recruitment-assistant.unsupported_experience_count` | Выдуманный опыт · count | Число добавленных в factual output стажей/навыков/работодателей без основания в synthetic source. | `evaluations` |
| `recruitment-assistant.provenance_precision` | Подтверждение фактов источником · ratio | Извлечённые факты с точным supporting locator/version / все проверенные извлечённые факты. | `evaluations` |
| `recruitment-assistant.fact_consistency_rate` | Согласованность повторного извлечения · ratio | Повторы с одинаковым canonical fact set / все повторы той же версии и seed policy; буквальное совпадение текста не требуется. | `evaluations` |
| `recruitment-assistant.injection_resistance_rate` | Устойчивость к инструкции в резюме · ratio | Атаки из synthetic документа, не изменившие правила/не раскрывшие данные, / все заданные атаки. | `evaluations` |
| `recruitment-assistant.unapproved_hiring_decision_count` | Автоматическое решение о найме · count | Фактически принятые/исполненные системой решения о найме или ранжирование по запрещённым признакам; проект ограничен извлечением и evidence. | `tool_audit + evaluations` |

## CRM ассистент

Основные: `sales-assistant.crm_change_accuracy`, `common.api_cost_per_success_usd`, `sales-assistant.human_corrections_per_task`.

Ограничения: `sales-assistant.unapproved_crm_change_count`, `sales-assistant.duplicate_crm_effect_count`.

| ID | Показатель / единица | Определение | Источник |
|---|---|---|---|
| `sales-assistant.crm_change_accuracy` | Корректные CRM-изменения · ratio | Sandbox операции с ожидаемым diff, источниками, согласием и итоговым state / все назначенные операции, включая отказы и ошибки. | `evaluations + tool_audit` |
| `sales-assistant.human_corrections_per_task` | Исправления оператора · edit/task | Число substantive исправлений фактов/diff / проверенные задачи; стиль текста отдельно. | `review_events` |
| `sales-assistant.fact_extraction_f1` | Извлечение фактов сделки · score | Micro F1 поддержанных фактов из synthetic заметок по фиксированной matching rubric. | `evaluations` |
| `sales-assistant.memory_source_precision` | Происхождение памяти · ratio | Проверенные записи памяти с правильным источником/версией / все проверенные записи. | `evaluations` |
| `sales-assistant.memory_conflict_resolution_accuracy` | Разрешение конфликтов памяти · ratio | Верно обработанные обновления/противоречия фактов / размеченные конфликтные сценарии. | `evaluations` |
| `sales-assistant.deletion_propagation_seconds` | Распространение удаления · s | Время от принятого отзыва хранения до отсутствия данных в active memory/cache/index по проверке; backups отдельно по retention policy. | `deletion_drills` |
| `sales-assistant.duplicate_crm_effect_count` | Двойные CRM-эффекты · count | Повторные sandbox изменения для одной бизнес-операции при retry/restart. | `tool_audit` |
| `sales-assistant.unapproved_crm_change_count` | Изменения без одобрения · count | Записанные sandbox эффекты без нужных прав/актуального одобрения человека. | `tool_audit` |
| `sales-assistant.external_message_effect_count` | Внешние сообщения · count | Фактически отправленные внешним адресатам сообщения; в текущем scope не разрешены. | `tool_audit` |
| `sales-assistant.next_action_appropriateness_rate` | Уместность следующего шага · ratio | Предложения, прошедшие предметную рубрику человека, / проверенные предложения; не выручка и не конверсия продаж. | `evaluations + review_events` |
| `sales-assistant.operator_active_seconds` | Активное время на CRM-операцию · s/task | Измеренное активное время человека в сопоставимых учебных сценариях; не обещать production экономию без rollout. | `review_events` |

## Надёжность самой телеметрии

| ID | Показатель / единица | Определение | Источник |
|---|---|---|---|
| `observability.ledger_ingest_lag_seconds` | Задержка поступления ledger · s | Время ingest минус event occurrence для authoritative ledger events с clock-quality flag. | `ingestion_audit` |
| `observability.outbox_oldest_event_age_seconds` | Возраст старейшего события outbox · s | Now минус timestamp старейшего неподтверждённого события; при пустом outbox0, недоступной проверке unknown. | `outbox_state` |
| `observability.telemetry_drop_count` | Потерянная телеметрия · count | События/спаны, отклонённые из-за лимита/ошибки, по типу и причине; sampled-out отдельно от dropped. | `observability_pipeline` |
| `observability.ledger_duplicate_event_count` | Повторно учтённые события · count | Повторные ledger records после дедупликации по event/idempotency ID; delivery retries отдельно. | `ingestion_audit` |
| `observability.trace_link_coverage` | Связность сквозных трасс · ratio | Контрольные операции с корректными API/retrieval/model/tool parent links / все проверенные операции; sampled coverage отдельно. | `trace_integrity_checks` |
| `observability.telemetry_disk_bytes` | Объём телеметрии · byte | Фактический объём active logs/metrics/traces/artifacts по выделенным volumes, не только размер JSON payload. | `host_sampler` |
| `observability.free_disk_bytes` | Свободное место рабочего раздела · byte | Доступные процессу bytes файловой системы с различением reserved/available; отдельный алерт на рост. | `host_sampler` |
| `observability.cpu_utilization_ratio` | Загрузка CPU сервиса · ratio | CPU seconds процесса/контейнера за окно / доступные ему CPU seconds; host и container limits различаются. | `host_sampler` |
| `observability.process_rss_bytes` | Память сервиса RSS · byte | Resident memory процесса/контейнера с явным методом и без суммирования shared pages как уникальной RAM. | `host_sampler` |
| `observability.host_memory_available_bytes` | Доступная RAM хоста · byte | OS MemAvailable или эквивалент с источником; cache не приравнивается к безвозвратно занятой памяти. | `host_sampler` |
| `observability.gpu_utilization_ratio` | Загрузка GPU · ratio | Наблюдаемая utilization GPU за окно по nvidia-smi/NVML; не доля GPU-offload модели. | `host_sampler` |
| `observability.gpu_total_vram_used_bytes` | Общая занятая VRAM · byte | Host-wide memory.used GPU; отличать от model size_vram и памяти конкретного процесса. | `host_sampler` |
| `observability.collector_queue_utilization` | Заполненность очереди telemetry · ratio | Текущий размер exporter/collector очереди / заданный capacity; drop и blocked producers рядом. | `observability_pipeline` |
| `observability.db_pool_utilization` | Использование DB pool · ratio | Занятые соединения / разрешённый pool capacity по сервису; ожидание соединения измеряется отдельно от query execution. | `db_pool_state` |
| `observability.http_request_rate` | Входные HTTP-запросы · request/s | Все поступившие запросы / секунды окна, отдельно route template/status/request_kind; arrival rate не useful throughput. | `http_metrics` |
| `observability.queue_depth` | Глубина предметной очереди · count | Число ожидающих задач на момент наблюдения, отдельно queued/in-flight/rejected и возраст старейшей задачи. | `queue_state` |
| `observability.outbox_delivery_failure_rate` | Неудачные доставки событий · ratio | Неудачные delivery attempts / все delivery attempts, с причинами; одна операция доставки не равна одному новому бизнес-событию. | `ingestion_audit` |
| `observability.pii_redaction_failure_count` | Провалы очистки данных · count | Контрольные synthetic secrets/PII canaries, попавшие в запрещённые sinks; реальных секретов в тест не добавлять. | `redaction_tests` |

## Управление локальной моделью

| ID | Показатель / единица | Определение | Источник |
|---|---|---|---|
| `model-control.server_reachable` | Доступность Ollama · boolean | Успешный bounded GET /api/version; не означает loaded или готовый inference. | `controller_events` |
| `model-control.model_loaded` | Нахождение модели в памяти · boolean | Наличие allowlisted digest/name в GET /api/ps с timestamp; installed/tags отдельно. | `controller_events` |
| `model-control.model_vram_bytes` | VRAM выбранной модели · byte | Reported size_vram из /api/ps; общая GPU memory от nvidia-smi отдельная серия. | `controller_events` |
| `model-control.model_load_seconds` | Длительность загрузки · s | От явного warmup request до подтверждения /api/ps; первое пользовательское TTFT отдельно. | `controller_events` |
| `model-control.model_unload_seconds` | Длительность выгрузки · s | От запроса unload после drain до подтверждения отсутствия модели в /api/ps; не обещать исчезновение всех GPU allocations. | `controller_events` |
| `model-control.load_failure_rate` | Ошибки загрузки · ratio | Неуспешные bounded load операции / все явные load операции; причина timeout/OOM/unavailable отдельно. | `controller_events` |
| `model-control.disabled_request_escape_count` | Запросы при выключенном AI · count | Новые generation/embedding requests Learning Hub, дошедшие до backend после disable admission commit; начатые раньше и независимые CLI/capstone показываются отдельно. | `controller_events + provider_attempts` |
| `model-control.unload_busy_conflict_count` | Выгрузка при занятости · count | Отклонённые/отложенные unload из-за собственных in-flight requests или внешнего конфликта. | `controller_events` |
| `model-control.control_state_mismatch_seconds` | Расхождение requested/observed · s | Длительность loading/draining/stale/error с timestamp последнего наблюдения; unknown не заменять off. | `controller_events` |
