"""Authentication & RBAC (charter Phase D placeholder).

Defines the interface future OAuth2/RBAC wiring will implement. Disabled by
default (settings.auth_enabled=False) so v0.1.0 runs open for development.
"""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class User:
    username: str
    roles: list[str] = field(default_factory=list)

class AuthProvider:
    """Interface for pluggable auth (OIDC/OAuth2). To be implemented in v1.0.0."""
    def authenticate(self, token: str) -> User:  # pragma: no cover
        raise NotImplementedError

def require_role(user: User, role: str) -> bool:
    return role in user.roles
