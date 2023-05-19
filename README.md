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
docker run --rm -e ARM_VARS_USE_EXISTING=1 --env-file .env.dev -v $PWD:/cli/.tftest qubixds/cloudforge:dev -v tf validate dev -d .tftest/
```
