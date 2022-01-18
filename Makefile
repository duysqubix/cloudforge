
VERSION:=$(shell /bin/cat VERSION)

build:
	echo "Building application"
	go build -v

clean:
	go clean 
	rm ec
	
push:
	git tag $(VERSION)
	git push origin master