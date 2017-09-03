# Makefile for macos x

PLUGINNAME = ClusterPoints
EXTRAS = metadata.txt README.html
DIRECTORIES = forms icons libs README-Dateien

SOURCES	:= $(shell find $(DIRECTORIES) -name *.ui)
COMPILE	:= $(SOURCES:%.ui=%.py)

all: 
	$(foreach file,$(COMPILE),pyuic4 $(file:%.py=%.ui) > $(file);)

	mkdir -p $(HOME)/.qgis2/python/plugins/$(PLUGINNAME)

	cp -vf *.py $(HOME)/.qgis2/python/plugins/$(PLUGINNAME)
	cp -vf $(EXTRAS) $(HOME)/.qgis2/python/plugins/$(PLUGINNAME)

	$(foreach dir,$(DIRECTORIES),rsync -rupE $(dir) $(HOME)/.qgis2/python/plugins/$(PLUGINNAME)/;)

