from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

SECRET_KEY = "HelloWorldThisIsASecretKeyForJWTTokenGeneration"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24




def create_access_token(
    user_id: int,
    role: str,
    name: str
):
    expire = datetime.now(timezone.utc) + timedelta(
        hours=ACCESS_TOKEN_EXPIRE_HOURS
    )

    payload = {
        "id": user_id,
        "role": role,
        "name": name,
        "exp": expire
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token, expire.isoformat()


def verify_token(token: str):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:
        return None
    
    
def is_token_expired(token: str):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return False

    except JWTError:
        return True
    
def get_user_from_token(token: str):

    payload = verify_token(token)

    if not payload:
        return None

    return {
        "id": payload["id"],
        "role": payload["role"],
        "name": payload["name"]
    }