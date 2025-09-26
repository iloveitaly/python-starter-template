"""
Marketing opt-in, and other related functions generally require some sort of audit data.

This is a simple data structure to capture this from a fastapi request and stick it in a JSONB column.
"""

from datetime import datetime
from ipaddress import ip_address

from fastapi import Request
from pydantic import BaseModel as PydanticBaseModel
from pydantic import IPvAnyAddress
from whenever import Instant


class UserActionAuditData(PydanticBaseModel):
    ip_address: IPvAnyAddress
    build_version: str
    timestamp: datetime

    @classmethod
    def from_request(cls, request: "Request") -> "UserActionAuditData":
        from app.constants import BUILD_COMMIT
        from app.routes.dependencies.realip import client_ip_from_request

        client_ip = client_ip_from_request(request) or "0.0.0.0"

        return cls(
            ip_address=ip_address(client_ip),
            build_version=BUILD_COMMIT,
            timestamp=Instant.now().to_system_tz().py_datetime(),
        )
