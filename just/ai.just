AI_CLIENTS := "antigravity,cursor"

ai_setup:
    # install shared agent skills (claude/cursor/etc) into the global skills dir
    pnpx skills add https://github.com/iloveitaly/ai-skills -g --all

    mcp-add \
      --name terraform \
      --type stdio \
      --command "docker run -i --rm hashicorp/terraform-mcp-server:latest" \
      --scope project \
      --clients {{ AI_CLIENTS }}
