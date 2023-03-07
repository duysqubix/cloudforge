# Cloud Forge 
Manage Azure by providing tools to validate and deploy
infrastructure



### To use

Pull in docker image from qubix repositories.

`docker pull qubixds/cloudforge:latest` or the appropriate tag

You can test everything works by.. 

`docker run --rm qubixds/cloudforge:latest version` 


Now you can run your commands. Here are some samples.

To manage cloudtf files you need to supply a env file

```bash
docker run --env-file .env.dev \
    -v $PWD/.tftest:/cli/.tftest \
    qubixds/cloudforge:dev tf -v validate dev -d .tftest/
```
