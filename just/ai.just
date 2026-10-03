AI_CLIENTS := "antigravity,cursor"

ai_setup:
    mcp-add \
      --name terraform \
      --type stdio \
      --command "docker run -i --rm hashicorp/terraform-mcp-server:latest" \
      --scope project \
      --clients {{ AI_CLIENTS }}
