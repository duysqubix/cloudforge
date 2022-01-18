
all:
	echo "Building application"
	go build -v -o ../


clean:
	go clean 
	rm ../ec
	