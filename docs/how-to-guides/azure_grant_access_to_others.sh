#!/bin/bash          

# Fill in details in this section
resource_prefix="feathrazuretest"
other_user_principal_id="abcd"
subscription_id="abcd"

# need to install purviewcli:
python -m pip install purviewcli

# You don't have to modify the names below
resoruce_group_name="$resource_prefix"rg
storage_account_name="$resource_prefix"sto
storage_file_system_name="$resource_prefix"fs
synapse_workspace_name="$resource_prefix"spark
redis_cluster_name="$resource_prefix"redis
purview_account_name="$resource_prefix"purview
synapse_firewall_rule_name="$resource_prefix"firewall

# detect whether az cli is installed or not
if ! [ -x "$(command -v az)" ]; then
  echo 'Error: Azure CLI is not installed. Please follow guidance on https://aka.ms/azure-cli to install az command line' >&2
  exit 1
fi

az upgrade --all true --yes
# login if required
az account get-access-token
if [[ $? == 0 ]]; then
  echo "Logged in, using current subscriptions "
else
  echo "Logging in via az login..."
  az login --use-device-code
fi

az role assignment create --role "Storage Blob Data Contributor" --assignee "$other_user_principal_id" --scope "/subscriptions/$subscription_id/resourceGroups/$resoruce_group_name/providers/Microsoft.Storage/storageAccounts/$storage_account_name"
# to keyvalut
az synapse role assignment create --workspace-name $synapse_workspace_name --role "Synapse Contributor" --assignee $other_user_principal_id

# to purview
pv policystore putMetadataPolicy