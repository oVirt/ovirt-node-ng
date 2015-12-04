
DOTS = \
	ngn-flow-components.dot.png \
	ngn-flow.dot.png \
	build-flow.dot.png

all: $(DOTS)

%.dot.png: %.dot
	dot -Tpng -O $<
