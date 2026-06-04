########################################
# Deployment Resource State
########################################

variable "deployment_state_tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)

  default = {
    environment = "production"
    managed     = true
  }
}

# resource group to hold common terraform state for deployment
# IMPORTANT: (1) when bootstrapping a new azure account, this must be done FIRST!
#            this means commenting out other the rest of the azure config and running this first
resource "azurerm_resource_group" "tfstate" {
  name     = local.tfstate.resource_group
  location = local.location

  # TODO customize tags since this is distinct from the deployment resource group
  tags = var.deployment_state_tags
}

# IMPORTANT: (2) when bootstrapping a new azure account, this must be done second!
# by default, tf stores state in the local filesystem. We use remote storage state to sync between
# multiple devs and eliminate dependency on a single machine.
resource "azurerm_storage_account" "tfstate" {
  name                = local.tfstate.storage_account
  resource_group_name = azurerm_resource_group.tfstate.name
  location            = azurerm_resource_group.tfstate.location

  account_tier = "Standard"
  # locally redundant storage is the cheapest
  account_replication_type = "LRS"

  # we don't want to allow public access to the storage account
  # this will contain secrets and should only be accessible to users who have azure admin
  https_traffic_only_enabled    = true
  min_tls_version               = "TLS1_2"
  public_network_access_enabled = true

  # prevent anyone from configuring a blob to ever be public
  allow_nested_items_to_be_public = false

  tags = var.deployment_state_tags
}

resource "azurerm_storage_container" "tfstate" {
  name                  = local.tfstate.container
  storage_account_id    = azurerm_storage_account.tfstate.id
  container_access_type = "private"
}

# deployment locking is handled by storing the state of the deployment in a bucket
# IMPORTANT: (3) with a resource group and storage account in place, move to remote state storage
data "terraform_remote_state" "tfstate" {
  backend = "azurerm"

  config = {
    # this is not in the docs, but is really important!
    # https://github.com/hashicorp/terraform/issues/23515
    resource_group_name  = azurerm_resource_group.tfstate.name
    storage_account_name = azurerm_storage_account.tfstate.name
    container_name       = azurerm_storage_container.tfstate.name
    key                  = local.tfstate.key
  }
}
