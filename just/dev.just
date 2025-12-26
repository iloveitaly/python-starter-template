# misc devprod scripts

[script]
ngrok:
  DIRECTORY=$(basename $(pwd)) && cat << EOF > $TMP_DIRECTORY/ngrok.yml
  version: 2
  authtoken: $(yq '.agent.authtoken' ~/.config/ngrok/ngrok.yml)
  tunnels:
    javascript_server:
      proto: http
      addr: https://${JAVASCRIPT_SERVER_HOST}
      domain: ${DIRECTORY}.ngrok-free.app
      host_header: ${JAVASCRIPT_SERVER_HOST}
    python_server:
      proto: http
      addr: https://${PYTHON_SERVER_HOST}
      domain: ${DIRECTORY}-api.ngrok-free.app
      host_header: ${PYTHON_SERVER_HOST}
  EOF

  ngrok start --all --config $TMP_DIRECTORY/ngrok.yml
