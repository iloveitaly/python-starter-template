AI_CLIENTS := "antigravity,cursor"

# for additional ai configuration, see https://github.com/iloveitaly/dotfiles/blob/master/brew.sh#L88
ai_setup:
    pnpx skills add https://github.com/iloveitaly/ai-skills -g --all

    mcp-add \
      --name terraform \
      --type stdio \
      --command "docker run -i --rm hashicorp/terraform-mcp-server:latest" \
      --scope project \
      --clients {{ AI_CLIENTS }}

    mcp-add \
      --name posthog \
      --type http \
      --url "https://mcp.posthog.com/mcp" \
      --scope project \
      --clients {{ AI_CLIENTS }}

    mcp-add \
      --name sentry \
      --type http \
      --url "https://mcp.sentry.dev/mcp" \
      --scope project \
      --clients {{ AI_CLIENTS }}
