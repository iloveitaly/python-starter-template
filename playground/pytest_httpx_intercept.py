# https://til.simonwillison.net/pytest/pytest-httpx-debug

def intercept(request):
    from pprint import pprint
    import json

    print(request.url)
    pprint(json.loads(request.content))
    breakpoint()
    return True
