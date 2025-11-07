# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Custom targets for convenience
html:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo "Documentation built in $(BUILDDIR)/html"
	@echo "Open: $(BUILDDIR)/html/index.html"

clean:
	@rm -rf $(BUILDDIR)/*
	@echo "Cleaned build directory"

livehtml:
	@echo "Starting live reload server..."
	@sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)

# Install dependencies
install:
	@echo "Installing documentation dependencies..."
	pip install sphinx sphinx-rtd-theme sphinx-autobuild

# Check for broken links
linkcheck:
	@$(SPHINXBUILD) -M linkcheck "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Generate coverage report
coverage:
	@$(SPHINXBUILD) -M coverage "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo "Coverage report generated in $(BUILDDIR)/coverage/python.txt"
