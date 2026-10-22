IMAGE := spanish-local-holidays-calendar

.PHONY: build generate test shell

build:
	docker build -t $(IMAGE) .

generate: build
	mkdir -p output
	docker run --rm -v $(CURDIR)/output:/app/output $(IMAGE)

test: build
	docker run --rm -e PYTHONPATH=/app/src $(IMAGE) python -m pytest

shell: build
	docker run --rm -it -v $(CURDIR)/output:/app/output $(IMAGE) bash
