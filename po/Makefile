DATADIR = /usr/share/
LOCALEDIR = $(DATADIR)/locale
DOMAIN = fslint
INSTALL = $(shell ginstall --help >/dev/null 2>&1 && echo ginstall || echo install)
MSGFMT = $(shell msgfmt --help 2>&1 | grep -- "--check" >/dev/null && echo "msgfmt -c" || echo "msgfmt")

all: mo

#create pot file
$(DOMAIN).pot: ../fslint.glade ../fslint-gui
	xgettext          -d$(DOMAIN) -LGlade  ../fslint.glade -o $(DOMAIN).pot
	xgettext -k_ -kN_ -d$(DOMAIN) -LPython ../fslint-gui   -o $(DOMAIN).pot -j

#update all po fles
update-po: $(DOMAIN).pot
	for po in *.po; do \
		lingua=`basename $$po .po`; \
		mv $$lingua.po $$lingua.old.po; \
		if msgmerge -N -o $$lingua.po $$lingua.old.po $(DOMAIN).pot; then \
		    rm $$lingua.old.po; \
		else \
		    rm -f $$lingua.po; \
		    mv $$lingua.old.po $$lingua.po; \
		fi \
	done

#create all mo files
mo:
	for po in *.po; do \
		lingua=`basename $$po .po` ; \
		$(MSGFMT) -o $$lingua.mo $$po ; \
		mkdir -p locale/$$lingua/LC_MESSAGES/ ; \
		ln -f $$lingua.mo locale/$$lingua/LC_MESSAGES/$(DOMAIN).mo ; \
	done

#install mo files
install: mo
	for mo in *.mo; do \
		lingua=`basename $$mo .mo`; \
		$(INSTALL) -D --mode=644 $$lingua.mo $(DESTDIR)/$(LOCALEDIR)/$$lingua/LC_MESSAGES/$(DOMAIN).mo ; \
	done

clean:
	rm -Rf locale
	rm -f *.mo
