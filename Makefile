.PHONY: build publish example

build b: ## Build the package
	uv build

publish p: ## Publish to PyPI
	uv publish

example e: ## Run the example
	./example/run.sh