cursor_sync:
  # TODO add MCP sync
  cp .vscode/settings.json .cursor/settings.json

ngrok:
  # assumes localias is running
  ngrok http "https://${JAVASCRIPT_SERVER_HOST}" \
    --domain "$(basename $(pwd)).ngrok-free.app" \
    --host-header "${JAVASCRIPT_SERVER_HOST}"
