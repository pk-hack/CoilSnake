all: coilsnake_lib submodule

install: all
	python setup.py install

test: coilsnake_lib
	python setup.py test

coverage: coilsnake_lib
	script/coverage.sh

coilsnake_lib:
	python setup.py build_ext --inplace clean

submodule:
	git submodule init
	git submodule update

clean:
	python setup.py clean
