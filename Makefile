.PHONY: \
	lint clean build push tests


all: clean check build


check:
	autoflake --in-place -r podm

clean:
	rm -rf build dist

build: 
	python3 setup.py sdist bdist_wheel

push: build
	python3 -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

tests:
	nosetests --with-coverage --cover-html --cover-package=podm test/

