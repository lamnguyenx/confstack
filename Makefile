.PHONY: build publish

build b: ## Build the package
	uv build

publish p: ## Publish to PyPI
	uv publish