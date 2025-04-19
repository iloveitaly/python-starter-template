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
