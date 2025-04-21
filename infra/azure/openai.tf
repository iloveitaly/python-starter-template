# https://medium.com/@williamwarley/streamlining-ai-with-azure-a-practical-guide-to-deploying-azure-openai-with-terraform-and-azure-bcbd01bbc3cf
# https://github.com/mucsi96/aks-modules/blob/29f20ea4c56fe192816c2dbd9f4fa641502b7a19/modules/setup_ai/main.tf
# services x region: https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models?tabs=global-standard%2Cstandard-chat-completions#model-summary-table-and-region-availability

resource "azurerm_ai_services" "openai_service" {
  name                = "${local.base_name_alphanumeric}openai"
  resource_group_name = azurerm_resource_group.main.name

  # this seems to be the "primary" region for OpenAI, it has the most recent models
  location            = "eastus2"

  sku_name = "S0" # Example SKU, adjust based on actual requirements
}

resource "azurerm_cognitive_deployment" "openai_4_1" {
  # must match the model name you specify in the OpenAI API call
  name                 = "gpt-4.1-2025-04-14"
  cognitive_account_id = azurerm_ai_services.openai_service.id

  # https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models?tabs=global-standard%2Cstandard-chat-completions#o1-and-o1-mini-models
  model {
    format  = "OpenAI"
    name    = "gpt-4.1"
    version = "2025-04-14"
  }

  sku {
    name     = "GlobalStandard"
    capacity = 50
  }
}

resource "azurerm_cognitive_deployment" "openai_4_1_mini" {
  # must match the model name you specify in the OpenAI API call
  name                 = "gpt-4.1-mini-2025-04-14"
  cognitive_account_id = azurerm_ai_services.openai_service.id

  model {
    format  = "OpenAI"
    name    = "gpt-4.1-mini"
    version = "2025-04-14"
  }

  sku {
    name     = "GlobalStandard"
    capacity = 50
  }
}

# restricted based on this form: https://aka.ms/OAI/o1access
resource "azurerm_cognitive_deployment" "openai_o1" {
  name                 = "o1"
  cognitive_account_id = azurerm_ai_services.openai_service.id

  model {
    format  = "OpenAI"
    name    = "o1"
    version = "2024-12-17"
  }

  sku {
    name     = "GlobalStandard"
    capacity = 50
  }
}

# https://registry.terraform.io/providers/1Password/onepassword/latest/docs
resource "onepassword_item" "azure_openai_service" {
  vault = data.external.secrets.result["OP_VAULT_UID"]

  title    = "Azure ${local.environment} Open AI Service"
  category = "login"

  url      = azurerm_ai_services.openai_service.endpoint
  password = azurerm_ai_services.openai_service.primary_access_key

  tags = var.onepassword_tags
}
