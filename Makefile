
VERSION:=$(shell /bin/cat VERSION)

build:
	echo "Building application"
	go build -ldflags="-X 'main.VERSION=$(VERSION)'" -o ec

version: build 
	./ec version

clean:
	go clean 
	rm ec
	
push:
	git tag $(VERSION)
	git push origin master --tags