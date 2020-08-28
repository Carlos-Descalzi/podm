.PHONY: \
	lint clean build push tests


all: clean build

clean:
	rm -rf build dist
build: lint
	python3 setup.py sdist bdist_wheel

push: build
	python3 -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

tests:
	nosetests test/

lint:
	black podm test
