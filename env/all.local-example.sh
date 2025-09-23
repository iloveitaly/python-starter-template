# NOTE helpful for "global" overrides if you are using a non-standard setup

# if you don't want to setup 1p auth via macOS, or you don't want to enter your 1p password
# when running `op` commands, you can set the token here. `just secrets_local-service-token`
# export OP_SERVICE_ACCOUNT_TOKEN=

# specify the 1p account that should be used to source secrets via `op read`
# useful if you have multiple 1p accounts, otherwise does not need to be set
# avoid committing to source control if you are security paranoid
# export OP_ACCOUNT=yourdomain.1password.com

# if your services are not hosted via orb stack
# export DATABASE_HOST=localhost
# export REDIS_HOST=localhost
# export SMTP_HOST=localhost

# azure does not allow for subscriptions to be set via an ENV var:
# https://stackoverflow.com/questions/38475104/azure-cli-how-to-change-subscription-default
# this forces the subscription to be set to the current subscription for this project

# watch_file ~/.azure/config
# AZURE_SUBSCRIPTION_ID=YOUR-UUID-ID
# az account set --subscription $AZURE_SUBSCRIPTION_ID
