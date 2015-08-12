TARBALL=sqlminus.current-macos.tgz
TOP=/usr/local/sqlminus

# first make install, so that the revision number is bumped.
# then commit, so that that revision number is tied to the source.

foo:
	@echo install, package, upload, cmp

install:
	./patch_version sqlminus.py
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
	scp sqlminus mhn:public_html/sqlminus/source-packages
	scp sqlminus.py mhn:public_html/sqlminus/source-packages

cmp:
	@-cmp sqlminus    $(TOP)/bin/sqlminus
	@-cmp sqlminus.py $(TOP)/bin/sqlminus.py
