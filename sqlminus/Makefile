TARBALL1=sqlminus.current-macos-small.tgz
TARBALL2=sqlminus.current-macos-full.tgz
TOP=/usr/local/sqlminus

# first make install, so that the revision number is bumped.
# then commit, so that that revision number is tied to the source.

foo:
	@echo install, package, upload, diff

install:
	# put rm first to check for proper sudo
	rm -f          $(TOP)/bin/sqlminus
	./patch_version sqlminus.py
	cp sqlminus    $(TOP)/bin/sqlminus
	chmod 555      $(TOP)/bin/sqlminus
	rm -f          $(TOP)/bin/sqlminus.py
	cp sqlminus.py $(TOP)/bin/sqlminus.py
	chmod 555      $(TOP)/bin/sqlminus.py

package:
	rm -f /tmp/$(TARBALL2)
	tar czf /tmp/$(TARBALL2) $(TOP)

upload1:
	rm -f /tmp/$(TARBALL1)
	tar czf /tmp/$(TARBALL1) $(TOP)/bin/sqlminus.py
	scp /tmp/$(TARBALL1) mhn:public_html/sqlminus
	scp sqlminus mhn:public_html/sqlminus/source-packages
	scp sqlminus.py mhn:public_html/sqlminus/source-packages

upload2:
	rm -f /tmp/$(TARBALL2)
	tar czf /tmp/$(TARBALL2) $(TOP)
	scp /tmp/$(TARBALL2) mhn:public_html/sqlminus

upload: upload1 upload2
	@echo done uploading

diff:
	@-diff sqlminus    $(TOP)/bin/sqlminus
	@-diff sqlminus.py $(TOP)/bin/sqlminus.py
