# sourced from TF_VAR_AZURE_SUBSCRIPTION_ID ENV var
variable "AZURE_SUBSCRIPTION_ID" {
  description = "Azure subscription ID"
  type        = string
  default     = ""
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)

  default = {
    environment = "production"
    managed     = true
  }
}

# 1Password Configuration
variable "OP_VAULT_UID" {
  description = "1Password vault UID for storing secrets"
  type        = string
  default     = ""
}

# similar to cloud resources, tag all tf-created 1p entries with a specific map
variable "onepassword_tags" {
  description = "A map of tags to add to all opentofu-generated 1p items"
  type        = list(string)

  default = [
    "terraform-managed"
  ]
}
