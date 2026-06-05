locals {
  # project name, without any non-alphanumeric characters, or environment indicators
  name_root = "yourapp"

  # configuration to store tf state for ability for multiple devs to deploy
  tfstate = {
    # this must be globally unique across all azure accounts. letters only!
    storage_account = "${local.name_root}tfstate"
    # resource group should be distinct from the resource group of the deployment
    resource_group = "${local.name_root}-tfstate"
    container      = "${local.name_root}-tfstate"
    key            = "${local.environment}.tfstate"
  }

  azure_subscription_id = var.AZURE_SUBSCRIPTION_ID

  # eastus2 is a "hero" region and has the best AI stuff and the most SKUs
  # however, it runs out of capacity on popular SKUs and is more expensive
  # when we originally set this up, eastus2 was out of capacity so we switched to westus3
  location = "westus3"

  # add the environment to the root name used for all other services
  environment = "prod"
  name        = "${local.name_root}-${local.environment}"

  # azure requires alpha numeric chars only in many places
  name_alphanumeric = replace(local.name, "/[^a-zA-Z0-9]/", "")
}
