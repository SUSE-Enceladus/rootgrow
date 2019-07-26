version := $(shell python -c 'from rootgrow.version import __VERSION__; print(__VERSION__)')

build: check test
	rm -f dist/*
	# create setup.py variant for rpm build.
	# delete module versions from setup.py for building an rpm
	# the dependencies to the python module rpm packages is
	# managed in the spec file
	sed -ie "s@>=[0-9.]*'@'@g" setup.py
	# build the sdist source tarball
	python setup.py sdist
	# restore original setup.py backed up from sed
	mv setup.pye setup.py
	# provide rpm source tarball
	mv dist/rootgrow-${version}.tar.gz dist/rootgrow.tar.gz
	# update rpm changelog using reference file
	helper/update_changelog.py --since package/rootgrow.changes > \
		dist/rootgrow.changes
	helper/update_changelog.py --file package/rootgrow.changes >> \
		dist/rootgrow.changes
	# update package version in spec file
	cat package/rootgrow-spec-template \
		| sed -e s'@%%VERSION@${version}@' \
		> dist/rootgrow.spec

.PHONY: test
test:
	tox -e unit_py3

check:
	tox -e check
