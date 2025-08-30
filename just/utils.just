#######################
# Utilities
#######################

# build commands generate a lot of output and when `[script]` is used no commands are echo'd, this lets us make build
# output easier to read in CI.
@_banner_echo BANNER:
	# TODO use style tags from justfile
	# TODO I wonder if sending an endgroup when one isn't started will cause issues.
	([[ -n "${CI:-}" ]] && echo "::endgroup::") || true
	([[ -n "${CI:-}" ]] && echo "::group::{{BANNER}}") || true
	# two spaces added because of the '# ' prefix on the banner message
	banner_length=$(echo -n "{{BANNER}}  " | wc -c) && \
	printf "\n\033[0;36m%${banner_length}s#\033[0m\n" | tr " " "#" && \
	printf "\033[0;36m# %s   \033[0m\n" "{{BANNER}}" && \
	printf "\033[0;36m%${banner_length}s#\033[0m\n\n" | tr " " "#"

# prevent a script from running if not in development mode
@_dev_only:
	[[ "${PYTHON_ENV:-}" = "development" ]] || { echo "error: PYTHON_ENV must be set to 'development'"; exit 1; }

# a more lazy _dev_only that can be used in contexts where the PYTHON_ENV is not set, which most commonly occurs when direnv is failing
# the main use case for this is generating 1P account tokens; if no token exists or the token is expired, direnv could fail
@_not_production:
	[[ -z "${PYTHON_ENV:-}" || "${PYTHON_ENV}" = "development" || "${PYTHON_ENV}" = "test" ]] || { echo "error: PYTHON_ENV is not empty or development"; exit 1; }
