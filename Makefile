
VERSION:=$(shell /bin/cat VERSION)

build:
	echo "Building application"
	go build -ldflags="-X 'main.VERSION=$(VERSION)'" -o ec

build_dev:
	echo "Building development application"
	go build -ldflags="-X main.VERSION=$(VERSION)-dev'" -o ec-dev


version: build 
	./ec version

version_dev: build_dev
	./ec-dev version

install: clean version
	cp ec /usr/bin/

install_dev: clean_dev version_dev
	cp ec-dev /usr/bin 

clean:
	go clean 
	rm -f ec
	rm -f /usr/bin/ec 
	

clean_dev:
	go clean
	rm -f ec-dev 
	rm -f /usr/bin/ec-dev 

push: 
	git tag $(VERSION)
	git push origin master --tags
