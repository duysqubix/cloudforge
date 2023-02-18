from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
import logging

VAULT_URL_BASE = "https://{}.vault.azure.net"

class AzureKeyVault:
    """Class to access secrets from an Azure Key Vault."""
    
    def __init__(self, vault_name: str, credential: ClientSecretCredential) -> None:
        """
        Initialize a new instance of the AzureKeyVault class.

        Args:
            vault_name (str): The name of the Azure Key Vault.
            credential (ClientSecretCredential): The credential object for accessing the Key Vault.
        """
        vault_url = VAULT_URL_BASE.format(vault_name)
        self.secret_client = SecretClient(vault_url, credential=credential)

    def get_secrets(self):
        """
        Get all the secrets in the Azure Key Vault.

        Returns:
            dict: A dictionary containing the names and values of all the secrets in the Azure Key Vault.
        """
        secrets = dict()
        for secret_properties in self.secret_client.list_properties_of_secrets():
            secret = self.secret_client.get_secret(secret_properties.name)
            logging.info("Storing secret: [%s]", secret.name)
            secrets[secret.name] = secret.value
        return secrets

                
if __name__ == "__main__":
    import logging 
    logging.basicConfig(level=logging.INFO)
    from azure.identity import ClientSecretCredential
    auth = ClientSecretCredential("da617b61-ca50-405b-abc8-314c0148fe06", 
                                  "98b6a09f-672c-41f1-9939-e2e1398c7aec", 
                                  "DJA8Q~~66on.m.zIZhoV148sRssH7I3Txr3Aab9F")
    akv = AzureKeyVault("qubixdsectest", auth)
    print(akv.get_secrets())