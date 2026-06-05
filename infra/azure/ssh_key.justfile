# NOTE: We generate and manage the SSH key via 1Password CLI (op) and this Justfile rather than Terraform.
#
# The 1P tf provide does not support SSH key generation. This file works around that limitation and should only be run
# a single time to generate the key, although new devs / machines can run this to extract the generated key from the 1P
# environment.

OP_VAULT_ID := env_var("OP_VAULT_UID")
OP_AZURE_VM_SSH_KEY_ITEM := "Azure Dokku SSH Key"
AZURE_SSH_KEY_FILE_NAME_PREFIX := "azure_vm_ssh_key"

[script]
ssh_generate:
    echo "Checking for existing SSH key '{{ OP_AZURE_VM_SSH_KEY_ITEM }}' in vault..."

    # Attempt to get the item; suppress errors if it doesn't exist
    if ITEM_ID=$(op item get "{{ OP_AZURE_VM_SSH_KEY_ITEM }}" --vault "{{ OP_VAULT_ID }}" --format json 2>/dev/null | jq -r '.id'); then
        echo "Key already exists."
    else
        echo "Key not found. Generating new SSH key..."
        ITEM_ID=$(op item create \
            --category "SSH Key" \
            --title "{{ OP_AZURE_VM_SSH_KEY_ITEM }}" \
            --vault "{{ OP_VAULT_ID }}" \
            --ssh-generate-key=ed25519 \
            --format json | jq -r '.id')
    fi

    echo "SSH Key Item UUID: $ITEM_ID"

    # Export the keys using the immutable UUID
    just ssh_export "$ITEM_ID"

# Extract ssh keys from 1p for access from azure terraform
[script]
ssh_export item_id:
    pub="{{ AZURE_SSH_KEY_FILE_NAME_PREFIX }}.pub"
    pem="{{ AZURE_SSH_KEY_FILE_NAME_PREFIX }}.pem"

    if [[ ! -f "$pub" ]]; then
        op read "op://{{ OP_VAULT_ID }}/{{ item_id }}/public key" --out-file "$pub"
    else
        echo "Skipping public key export; $pub already exists."
    fi

    if [[ ! -f "$pem" ]]; then
        # Note that the format is really important here!
        op read "op://{{ OP_VAULT_ID }}/{{ item_id }}/private key?ssh-format=openssh" --out-file "$pem"
        chmod 600 "$pem"
    else
        echo "Skipping private key export; $pem already exists."
    fi
