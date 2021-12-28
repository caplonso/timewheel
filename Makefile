SHELL=/bin/bash

build:
	@python setup.py bdist_wheel

check:
	@twine check dist/*

upload:
	@twine upload dist/*