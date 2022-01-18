package utils

import (
	"context"
	"fmt"
	"strings"

	"github.com/Azure/azure-sdk-for-go/profiles/latest/keyvault/keyvault"
	"github.com/Azure/go-autorest/autorest/azure/auth"
	"github.com/op/go-logging"
)

func GetKeyVaultSecrets(vaultName *string, auth *AzureServicePrincipal) *map[string]string {
	logger.Info("Initializing Azure KeyVault Client")
	keyVaultClient := getKeyVaultClient(&auth.clientId, &auth.clientSecret, &auth.tenantId)

	vaultUri := fmt.Sprintf("https://%s.vault.azure.net", *vaultName)

	var maxResults int32 = 25

	logger.Infof("Obtaining Secrets")
	keys, err := keyVaultClient.GetSecrets(context.Background(), vaultUri, &maxResults)

	if err != nil {
		panic(err)
	}

	secrets := make(map[string]string)
	pageNum := 0
	for {
		values := keys.Values()

		if values == nil {
			break
		}
		logger.Infof("Processing Page: %v", pageNum)

		for _, val := range values {
			secretName := getSecretNameFromId(val.ID)
			secretValue := getSecret(&vaultUri, keyVaultClient, &secretName)
			secrets[secretName] = secretValue
			logger.Infof("Storing secret: [%v]=[%v]", secretName, logging.Redact(secretValue))
		}
		err := keys.NextWithContext(context.Background())
		if err != nil {
			panic(err)
		}
		pageNum++
	}

	return &secrets
}

func getSecretNameFromId(secretId *string) string {
	split := strings.Split(strings.TrimSpace(*secretId), "/")
	return split[len(split)-1]
}

func getKeyVaultClient(clientId, clientSecret, tenantId *string) (client keyvault.BaseClient) {
	keyvaultClient := keyvault.New()
	clientCredentialConfig := auth.NewClientCredentialsConfig(*clientId, *clientSecret, *tenantId)

	clientCredentialConfig.Resource = "https://vault.azure.net"
	authorizer, err := clientCredentialConfig.Authorizer()

	if err != nil {
		fmt.Printf("Error occured while creating azure KV authroizer %v ", err)

	}
	keyvaultClient.Authorizer = authorizer

	return keyvaultClient
}

func getSecret(vaultUri *string, keyvaultClient keyvault.BaseClient, secretName *string) string {

	res, err := keyvaultClient.GetSecret(context.Background(), *vaultUri, *secretName, "")

	if err != nil {
		fmt.Printf("Error occured Get Secret %s , %v", *secretName, err)
	}

	return *res.Value
}
