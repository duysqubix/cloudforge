
VERSION:=$(shell /bin/cat VERSION)

build:
	echo "Building application"
	go build -ldflags="-X 'main.VERSION=$(VERSION)'" -o ec

version: build 
	./ec version

install: clean version
	cp ec /usr/bin/

clean:
	go clean 
	rm -f ec
	rm -f /usr/bin/ec 
	
push: 
	git tag $(VERSION)
	git push origin master --tags
