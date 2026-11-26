"""LAB01: шаблон ученика. Сетевых вызовов в заготовке нет."""

from __future__ import annotations

import asyncio
from typing import Any

from openai import AsyncOpenAI


def read_config() -> dict[str, Any]:
    # TODO: читать LLM_* из окружения; defaults — local, loopback и qwen2.5-coder:7b.
    # TODO: до создания клиента отклонять внешний host, userinfo, иной порт,
    # перенаправляющий transport/proxy и облачную модель в локальном режиме.
    # TODO: cloud в LAB01 всегда отклонять: бюджет пока 0, ключ не даёт разрешение.
    raise NotImplementedError("Реализуйте проверяемый контракт конфигурации")


def create_client(config: dict[str, Any]) -> AsyncOpenAI:
    # TODO: официальный AsyncOpenAI; явные base_url, api_key, timeout, max_retries=0.
    # TODO: исключить redirect/proxy-выход за loopback средствами закреплённого SDK.
    # TODO: закрытие клиента обеспечить у вызывающего кода.
    raise NotImplementedError("Создайте локальный клиент официального SDK")


async def extract_ticket(client: AsyncOpenAI, model: str, text: str) -> str:
    # TODO: chat.completions.create с await; system/user messages; ограниченный вывод.
    # TODO: проверить наличие choices/message/content, не печатая исходный текст.
    raise NotImplementedError("Выполните один локальный запрос Chat Completions")


def validate_extraction(content: str) -> dict[str, str]:
    # TODO: самостоятельно описать TicketExtraction через Pydantic, extra='forbid'.
    # TODO: category=billing|technical|other, urgency=low|normal|high,
    # summary — строка 1–120 символов; не принимать пустой JSON как успех.
    # TODO: различить JSON syntax и schema error, вернуть проверенные значения.
    raise NotImplementedError("Реализуйте схему и валидацию ответа")


async def main() -> None:
    # TODO: конфигурация -> клиент -> локальный запрос -> валидация -> краткий результат.
    # TODO: отдельно обработать timeout/connection/API/JSON/schema; без бесконечных retries.
    # TODO: измерить полную latency monotonic clock; закрыть клиент при ошибке/отмене.
    # TODO: только синтетические данные; журнал без ключа, prompt и персональных данных.
    raise NotImplementedError("Сначала сохраните свою попытку LAB01")


if __name__ == "__main__":
    asyncio.run(main())
