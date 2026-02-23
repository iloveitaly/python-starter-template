"""
Unauthenticated HTML routes.
"""

from datetime import datetime

from fastapi import APIRouter, Depends

from app.templates import render_template

from activemodel.session_manager import aglobal_session

unauthenticated_html = APIRouter(
    dependencies=[
        # NOTE this line could not be more important, look at the underlying implementation!
        Depends(aglobal_session),
    ],
)


# NOTE important to NOT use `async` for methods which perform sync IO, it's better to use non-async functions since they will then
#      be run in a threadpool and much better performance
@unauthenticated_html.get("/hello")
def index():
    return render_template("routes/index.html", {"date": datetime.now()})
