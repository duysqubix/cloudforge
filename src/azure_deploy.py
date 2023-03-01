"""A deployer class to deploy a template on Azure"""
import os.path
import json
from haikunator import Haikunator
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode


class Deployer(object):
    """Initialize the deployer class with subscription, resource group and public key.

    :raises IOError: If the public key path cannot be read (access or not exists)
    :raises KeyError: If AZURE_CLIENT_ID, AZURE_CLIENT_SECRET or AZURE_TENANT_ID env
        variables or not defined
    """

    name_generator = Haikunator()

    def __init__(
        self, subscription_id, resource_group, pub_ssh_key_path="~/id_rsa.pub"
    ):
        subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
        credentials = ServicePrincipalCredentials(
            client_id=os.environ["AZURE_CLIENT_ID"],
            secret=os.environ["AZURE_CLIENT_SECRET"],
            tenant=os.environ["AZURE_TENANT_ID"],
        )

        self.subscription_id = subscription_id
        self.resource_group = resource_group

        self.credentials = credentials
        self.client = ResourceManagementClient(
            self.credentials,
            self.subscription_id,
        )

    def deploy(self, template, parameters):
        """Deploy the template to a resource group."""
        self.client.resource_groups.create_or_update(
            self.resource_group, {"location": os.environ["AZURE_RESOURCE_LOCATION"]}
        )

        parameters = {k: {"value": v} for k, v in parameters.items()}

        deployment_properties = {
            "properties": {
                "mode": DeploymentMode.incremental,
                "template": template,
                "parameters": parameters,
            }
        }

        deployment_async_operation = self.client.deployments.begin_create_or_update(
            self.resource_group, self.name_generator.haikunate(), deployment_properties
        )
        deployment_async_operation.wait()

    def destroy(self):
        """Destroy the given resource group"""
        self.client.resource_groups.delete(self.resource_group)
