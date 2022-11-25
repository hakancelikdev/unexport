dev:
	pip install -e .[tests]
	pip install pre-commit

lint:
	git add .
	pre-commit run --all-files

test:
	pytest tests -x -v --disable-warnings

clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf .tox
	rm -rf build

push:
	git push origin head

amend:
	git add .
	git commit --amend --no-edit
	git push origin head -f

stable:
	git checkout main
	git branch -D stable
	git checkout -b stable
	git push origin head -f
	git checkout main

git:
	git config --local user.email "hakancelikdev@gmail.com"
	git config --local user.name "Hakan Celik"
