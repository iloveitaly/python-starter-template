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


@unauthenticated_html.get("/hello")
async def index():
    return render_template("routes/index.html", {"date": datetime.now()})
