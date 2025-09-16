from typing import Any

import orjson
from fastapi.responses import JSONResponse


class ORJSONSortedResponse(JSONResponse):
    """
    Lifted from the non-sorted fastapi-built version. ORJSONResponse is much faster than JSONResponse, but it does
    not respect the order of the keys:

    https://stackoverflow.com/questions/64408092/how-to-set-response-class-in-fastapi
    """

    def render(self, content: Any) -> bytes:
        return orjson.dumps(content, option=orjson.OPT_NON_STR_KEYS)
