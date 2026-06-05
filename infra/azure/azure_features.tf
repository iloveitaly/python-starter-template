# On a brand new account certain features need to be enabled otherwise you'll encounter strange permission issues I don't fully understand why this is the case but enabling these features using the following as your modules work for me.
# This was true as of 2026-06-05

# Encryption at Host encrypts your virtual machine's data directly on the physical server it runs on, ensuring the data is fully secure *before* it travels across Azure's internal network to your storage disk.
# This protects your data as it's traveling across the internal Azure network. Newer chips eliminate any CPU cost here.

resource "azurerm_resource_provider_registration" "compute" {
  name = "Microsoft.Compute"

  feature {
    name       = "EncryptionAtHost"
    registered = true
  }
}

resource "azurerm_resource_provider_registration" "communication" {
  name = "Microsoft.Communication"
}
