from datetime import datetime, timedelta, timezone
import secrets

from core.config import settings
from core.schemas import AuthSession, TokenUser


def issue_session(user: TokenUser) -> AuthSession:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.session_ttl_hours)
    return AuthSession(
        token=secrets.token_urlsafe(32),
        expiresAt=expires_at.isoformat(),
        user=user,
    )
