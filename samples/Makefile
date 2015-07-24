# Makefile for running and building tests


PYTHON=python
SQLPLUS=sqlplus
CONNSTR=orapig/tiger

all:
	@echo Usage: 
	@echo "make install-samples   Install sample Oracle packages"
	@echo "make export-samples    Export python wrappers for sample packages"
	@echo "make clean             Remove generated files"
	@echo " "
	@echo Macros:
	@echo "CONNSTR                Oracle connection string"
	@echo "PYTHON                 Path to the 'python' binary"
	@echo "SQLPLUS                Path to the 'sqlplus' binary"


install-samples: alltypes.sql keyword.sql tiny.sql
	$(SQLPLUS) $(CONNSTR) < alltypes.sql
	$(SQLPLUS) $(CONNSTR) < keyword.sql
	$(SQLPLUS) $(CONNSTR) < tiny.sql

uninstall-samples: uninstall.sql
	$(SQLPLUS) $(CONNSTR) < uninstall.sql

export-samples: alltypes.py keyword.py tinysample.py

%.py: 
	$(PYTHON) ../orapig.py -C$(CONNSTR) $* > $*.py || (rm $*.py && exit 1) 

test: unittests.py export-samples alltypes.py-regress tiny.py-regress keyword.py-regress
	$(PYTHON) unittests.py -C$(CONNSTR)
	@diff alltypes.py alltypes.py-regress
	@diff tinysample.py tiny.py-regress
	@diff keyword.py keyword.py-regress

update-regress: export-samples
	cp alltypes.py alltypes.py-regress
	cp tinysample.py tiny.py-regress
	cp keyword.py keyword.py-regress

clean:
	$(RM) alltypes.py keyword.py tinysample.py *.pyc
