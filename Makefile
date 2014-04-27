CCSCRIPT_SRC_DIR=ccscript_legacy/src
CCSCRIPT_BIN_DIR=$(CCSCRIPT_SRC_DIR)/bin
ASSETS_CCSCRIPT_DIR=coilsnake/assets/ccc

all: coilsnake ccscript

install: all
	python setup.py install

test: coilsnake
	python setup.py test

coilsnake:
	python setup.py build_ext --inplace clean

ccscript:
	git submodule init
	git submodule update
	cd $(CCSCRIPT_SRC_DIR) ; \
		make
	cp -r $(CCSCRIPT_BIN_DIR)/ccc $(CCSCRIPT_BIN_DIR)/lib $(ASSETS_CCSCRIPT_DIR)

clean:
	python setup.py clean
	find coilsnake/ -name \*.so | xargs rm
	cd $(CCSCRIPT_SRC_DIR) ; \
		make clean
	rm -r $(ASSETS_CCSCRIPT_DIR)/ccc $(ASSETS_CCSCRIPT_DIR)/lib