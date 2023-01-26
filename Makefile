BIN="ec"
GOPROJ="github.com/vorys-econtrol/ec"
BIN_OUTPUT=$(CURDIR)/bin/$(BIN)
VERSION=0.7.3


LDFLAGS_DEV="-w -X $(GOPROJ)/version.PreRelease=dev -X $(GOPROJ)/version.Version=$(VERSION)"
LDFLAGS_PROD="-w -s -X $(GOPROJ)/version.Version=$(VERSION)"

gotest:
	go test -v ./... && echo "Testing complete" || exit 1

godownload:
	go mod download

compile-modules:
	bash --noprofile $(CURDIR)/scripts/compile_modules.sh $(BIN)

package:
	mkdir -pv $(CURDIR)/releases
	zip -v -j $(CURDIR)/releases/ec-$(VERSION).zip $(CURDIR)/bin/*

upload: package
	gh -R github.com/duysqubix/ec-release release create $(VERSION) '$(CURDIR)/releases/ec-$(VERSION).zip' --generate-notes -t $(VERSION)

build-dev:
	go build -ldflags $(LDFLAGS_DEV) -o $(BIN_OUTPUT)

build-prod:
	go build -ldflags $(LDFLAGS_PROD) -o $(BIN_OUTPUT)

install:
	cp $(CURDIR)/bin/* /usr/local/bin

dev: gotest build-dev compile-modules 

release: gotest build-prod compile-modules package

.NOTPARALLEL:
.PHONY: generate
