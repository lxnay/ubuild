PREFIX = /usr
BINDIR = $(PREFIX)/bin
LIBDIR = $(PREFIX)/lib
PROGNAME = ubuild
DESTDIR = 

all:

install:
	install -d $(DESTDIR)$(PREFIX)/bin
	install -d $(DESTDIR)$(LIBDIR)/$(PROGNAME)
	install -d $(DESTDIR)$(LIBDIR)/$(PROGNAME)/core
	install -d $(DESTDIR)$(LIBDIR)/$(PROGNAME)/conf
	install -m 755 $(PROGNAME).py $(DESTDIR)$(LIBDIR)/$(PROGNAME)/.
	install -m 755 core/env_sourcer.sh $(DESTDIR)$(LIBDIR)/$(PROGNAME)/core/.
	install -m 644 conf/* $(DESTDIR)$(LIBDIR)/$(PROGNAME)/conf/.

	ln -sf "../$(shell basename $(LIBDIR))/$(PROGNAME)/$(PROGNAME).py" \
		$(DESTDIR)$(PREFIX)/bin/$(PROGNAME)

test:
	./ubuild_test.py
