PYTHON ?= .venv/bin/python

.PHONY: clean build publish commit release

clean:
	rm -rf dist/ build/ *.egg-info django_drf_mcp.egg-info

build: clean
	$(PYTHON) -m build

publish: build
	$(PYTHON) -m twine upload dist/*

commit:
	git add -A
	git commit -m "$(msg)"
	git push

release: commit publish
