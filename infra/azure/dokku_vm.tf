# https://github.com/Azure/terraform-azurerm-avm-res-compute-virtualmachine/tree/main
# Virtual Machine Configuration using Azure Verified Module (AVM)
# https://github.com/Azure/terraform-azurerm-avm-res-compute-virtualmachine

# You may need to manually run this:
# module.vm.azurerm_linux_virtual_machine.this[0]: Creating...
# ╷
# │ Error: creating Linux Virtual Machine (Subscription: "7570adec-2753-4a5c-8972-d1c57afa425b"
# │ Resource Group Name: "yourapp-prod"
# │ Virtual Machine Name: "yourapp-prod-vm"): performing CreateOrUpdate: unexpected status 400 (400 Bad Request) with error: InvalidParameter: The property 'securityProfile.encryptionAtHost' is not valid because the 'Microsoft.Compute/EncryptionAtHost' feature is not enabled for this subscription.
# │
# │   with module.vm.azurerm_linux_virtual_machine.this[0],
# │   on .terraform/modules/vm/main.linux_vm.tf line 1, in resource "azurerm_linux_virtual_machine" "this":
# │    1: resource "azurerm_linux_virtual_machine" "this" {
# │
# ╵
# az feature register --namespace Microsoft.Compute --name EncryptionAtHost

# Virtual Network for the VM
resource "azurerm_virtual_network" "main" {
  name                = "${local.name}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = local.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = var.tags
}

# Subnet for the VM
resource "azurerm_subnet" "internal" {
  name                 = "${local.name}-internal"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.2.0/24"]
}

# Network Security Group with basic rules
resource "azurerm_network_security_group" "vm" {
  name                = "${local.name}-vm-nsg"
  location            = local.location
  resource_group_name = azurerm_resource_group.main.name

  # Allow SSH
  security_rule {
    name                       = "SSH"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Allow HTTP
  security_rule {
    name                       = "HTTP"
    priority                   = 1002
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Allow HTTPS
  security_rule {
    name                       = "HTTPS"
    priority                   = 1003
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = var.tags
}

# Associate Network Security Group to Subnet
resource "azurerm_subnet_network_security_group_association" "vm" {
  subnet_id                 = azurerm_subnet.internal.id
  network_security_group_id = azurerm_network_security_group.vm.id
}

# Storage Account for boot diagnostics
# resource "azurerm_storage_account" "vm_diag" {
#   name                     = "${local.name_alphanumeric}vmdiag"
#   resource_group_name      = azurerm_resource_group.main.name
#   location                 = local.location
#   account_kind             = "StorageV2"
#   account_tier             = "Standard"
#   account_replication_type = "LRS"

#   tags = var.tags
# }

# Azure Verified Module for Virtual Machine
module "vm" {
  source  = "Azure/avm-res-compute-virtualmachine/azurerm"
  version = "~> 0.20.0"

  # Basic VM Configuration
  enable_telemetry    = false
  name                = "${local.name}-vm"
  location            = local.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"

  # B2 series has a CPU credit system; if we experience consistent high load, it may makes sense to use `Standard_B2ps_v2`
  # easiest way to get these is to run `az vm list-skus --location eastus2 --output table`
  # https://azure.microsoft.com/en-in/pricing/calculator/
  sku_size = "Standard_D2pls_v6"
  zone     = "2"

  # Operating System, latest Ubuntu LTS
  # NOTE: Ubuntu 24.04 is used because the Dokku SSH installation module does not support 26.04 yet.
  source_image_reference = {
    # list all OS publishers in the region
    # az vm image list-publishers --location eastus2 --output table
    publisher = "Canonical"
    # az vm image list-offers --location eastus2 --publisher Canonical --output table
    offer = "ubuntu-24_04-lts"
    # `az vm image list-skus --location eastus2 --publisher Canonical --offer ubuntu-24_04-lts --output table`
    sku     = "server-arm64"
    version = "latest"
  }

  # OS Disk Configuration
  os_disk = {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 60
  }

  # use SSD since we'll be hosting DB + Redis via Dokku on the machine
  data_disk_managed_disks = {
    data1 = {
      name                 = "${local.name}-vm-data1"
      lun                  = 0
      storage_account_type = "StandardSSD_LRS"
      disk_size_gb         = 100
      caching              = "ReadWrite"
    }
  }

  # Authentication - SSH Key
  disable_password_authentication = true
  admin_username                  = "yourapp"

  # SSH Keys
  account_credentials = {
    admin_credentials = {
      generate_admin_password_or_ssh_key = false
      # TODO we should pull the key name from a ENV var
      ssh_keys = [file("./azure_vm_ssh_key.pub")]
    }
  }


  network_interfaces = {
    network_interface_1 = {
      name = "${local.name}-vm-nic"
      ip_configurations = {
        ip_configuration_1 = {
          name                          = "${local.name}-vm-nic-ipconfig1"
          private_ip_subnet_resource_id = azurerm_subnet.internal.id

          create_public_ip_address = true
          public_ip_address_name   = "${local.name}-vm-nic-ipconfig1-publicip"
        }
      }
    }
  }

  # Boot Diagnostics
  boot_diagnostics = true

  # Cloud-Init Script
  custom_data = filebase64("${path.module}/cloud-init-data-disk.yaml")

  # can't use secure boot with ARM hosts yet

  # Tags
  tags = var.tags

  depends_on = [
    azurerm_subnet_network_security_group_association.vm,
    azurerm_resource_provider_registration.compute
  ]
}

# Store VM connection details in 1Password
resource "onepassword_item" "vm_connection" {
  vault = var.OP_VAULT_UID

  title    = "Azure ${local.environment} VM Connection"
  category = "login"

  url      = module.vm.virtual_machine_azurerm.public_ip_address # Just the IP address
  username = module.vm.admin_username

  section {
    label = "connection"

    field {
      label = "ssh-port"
      value = "22"
    }

    field {
      label = "vm-name"
      value = module.vm.resource.name
    }

    field {
      label = "resource-id"
      value = module.vm.resource.id
    }
  }

  tags = var.onepassword_tags

  depends_on = [
    module.vm
  ]
}
