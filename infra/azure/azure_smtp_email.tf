# Main Azure Communication Service (Hub)
resource "azurerm_communication_service" "main" {
  name                = "${local.name}-acs"
  resource_group_name = azurerm_resource_group.main.name
  data_location       = "United States"
}

# Email Communication Service (Container)
resource "azurerm_email_communication_service" "main" {
  name                = "${local.name}-email"
  resource_group_name = azurerm_resource_group.main.name
  data_location       = "United States"
}

# Azure-Managed Domain
resource "azurerm_email_communication_service_domain" "managed" {
  name              = "AzureManagedDomain"
  email_service_id  = azurerm_email_communication_service.main.id
  domain_management = "AzureManaged"
}

# Associate Domain with Communication Service
resource "azurerm_communication_service_email_domain_association" "main" {
  communication_service_id = azurerm_communication_service.main.id
  email_service_domain_id  = azurerm_email_communication_service_domain.managed.id
}

# Identity for SMTP Authentication
resource "azuread_application" "smtp_sender" {
  display_name = "${local.name}-smtp-sender"
}

resource "azuread_service_principal" "smtp_sender" {
  client_id = azuread_application.smtp_sender.client_id
}

resource "azuread_application_password" "smtp_sender" {
  application_id = azuread_application.smtp_sender.id
}

# Role assignment to allow sending
resource "azurerm_role_assignment" "smtp_sender" {
  scope                = azurerm_communication_service.main.id
  role_definition_name = "Communication and Email Service Owner"
  principal_id         = azuread_service_principal.smtp_sender.object_id
}

# Link Identity to ACS SMTP (Required for Relay)
resource "azapi_resource" "smtp_username" {
  type      = "Microsoft.Communication/communicationServices/smtpUsernames@2025-09-01"
  name      = "default-sender"
  parent_id = azurerm_communication_service.main.id

  body = {
    properties = {
      username           = azuread_application.smtp_sender.client_id
      entraApplicationId = azuread_application.smtp_sender.client_id
      tenantId           = data.azurerm_client_config.current.tenant_id
    }
  }
}

data "azurerm_client_config" "current" {}

# Store ACS SMTP Credentials in 1Password
resource "onepassword_item" "acs_smtp" {
  vault = var.OP_VAULT_UID

  title    = "${local.environment} ACS SMTP"
  category = "login"

  url      = "smtp.azurecomm.net"
  # Format required by Azure: <ACS_Resource_Name>.<App_ID>.<Tenant_ID>
  username = "${azurerm_communication_service.main.name}.${azuread_application.smtp_sender.client_id}.${data.azurerm_client_config.current.tenant_id}"
  password = azuread_application_password.smtp_sender.value

  section {
    label = "details"

    field {
      label = "port"
      value = "587"
    }

    field {
      label = "sender-domain"
      value = azurerm_email_communication_service_domain.managed.from_sender_domain
    }

    field {
      label = "smtp-auth-url"
      value = "smtp://${urlencode("${azurerm_communication_service.main.name}.${azuread_application.smtp_sender.client_id}.${data.azurerm_client_config.current.tenant_id}")}:${urlencode(azuread_application_password.smtp_sender.value)}@smtp.azurecomm.net:587"
    }
  }

  tags = var.onepassword_tags
}
