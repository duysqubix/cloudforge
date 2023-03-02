from haikunator import Haikunator
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode


class ArmDeployer:
    """A class to deploy an Azure Resource Manager template to an Azure subscription.

    Attributes:
        name_generator (Haikunator): An instance of the haikunator class to generate random names.
        subscription_id (str): The ID of the Azure subscription to deploy the template to.
        resource_group (str): The name of the resource group to deploy the template to.
        credentials (ServicePrincipalCredentials): Credentials to authenticate to the Azure API.
        client (ResourceManagementClient): A client for interacting with the Azure Resource Manager API.
    """

    name_generator = Haikunator()

    def __init__(
        self,
        subscription_id: str,
        resource_group: str,
        credentials: ServicePrincipalCredentials,
    ) -> None:
        """Initializes a new instance of the Deployer class.

        Args:
            subscription_id (str): The ID of the Azure subscription to deploy the template to.
            resource_group (str): The name of the resource group to deploy the template to.
            credentials (ServicePrincipalCredentials): Credentials to authenticate to the Azure API.
        """
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.credentials = credentials

        self.client = ResourceManagementClient(
            self.credentials,
            self.subscription_id,
        )

    def deploy(self, template: dict, parameters: dict) -> None:
        """Deploys an Azure Resource Manager template to the specified resource group.

        Args:
            template (dict): The ARM template as a dictionary.
            parameters (dict): The parameters to the ARM template as a dictionary.

        Raises:
            Exception: An error occurred while deploying the ARM template.
        """
        parameters = {k: {"value": v} for k, v in parameters.items()}

        # Construct the deployment properties object
        deployment_properties = {
            "properties": {
                "mode": DeploymentMode.incremental,
                "template": template,
                "parameters": parameters,
            }
        }

        # Start the deployment and wait for it to complete
        deployment_async_operation = self.client.deployments.begin_create_or_update(
            self.resource_group, self.name_generator.haikunate(), deployment_properties
        )
        deployment_async_operation.wait()
