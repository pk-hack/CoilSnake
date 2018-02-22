all: coilsnake_lib submodule

install: all
	python3 setup.py install

test: coilsnake_lib
	python3 setup.py test

coverage: coilsnake_lib
	script/coverage.sh

coilsnake_lib:
	python3 setup.py build_ext --inplace clean

submodule:
	git submodule init
	git submodule update

clean:
	python3 setup.py clean
