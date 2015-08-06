TARBALL=sqlminus.current-macos.tgz
TOP=/usr/local/sqlminus
foo:
	@echo install, package, upload, cmp

install:
	rm -f          $(TOP)/bin/sqlminus
	cp sqlminus    $(TOP)/bin/sqlminus
	chmod 555      $(TOP)/bin/sqlminus
	rm -f          $(TOP)/bin/sqlminus.py
	cp sqlminus.py $(TOP)/bin/sqlminus.py
	chmod 555      $(TOP)/bin/sqlminus.py

package:
	rm -f /tmp/$(TARBALL)
	tar czf /tmp/$(TARBALL) $(TOP)

upload:
	scp /tmp/$(TARBALL) mhn:public_html/sqlminus

cmp:
	@-cmp sqlminus    $(TOP)/bin/sqlminus
	@-cmp sqlminus.py $(TOP)/bin/sqlminus.py
