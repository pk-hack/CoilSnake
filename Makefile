install:
	python setup.py build_ext --inplace clean
clean:
	python setup.py clean
	find coilsnake/ -name \*.so | xargs rm