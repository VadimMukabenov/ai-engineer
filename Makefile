UV ?= uv
HUB := projects/learning-hub

.PHONY: setup test verify status serve readme llm-smoke
setup:
	$(UV) sync --project $(HUB) --dev
test:
	$(UV) run --project $(HUB) pytest -c $(HUB)/pyproject.toml $(HUB)/tests
verify:
	$(UV) run --project $(HUB) learning-hub --root . verify
status:
	$(UV) run --project $(HUB) learning-hub --root . status
readme:
	$(UV) run --project $(HUB) learning-hub --root . readme
serve:
	$(UV) run --project $(HUB) learning-hub --root . serve --host 127.0.0.1 --port 8765
llm-smoke:
	$(UV) run --project $(HUB) learning-hub --root . llm-smoke
