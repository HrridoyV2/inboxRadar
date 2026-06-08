import jwt
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

security = HTTPBearer()

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verifies that the provided HTTP Bearer token is a valid JWT signed with JWT_SECRET."""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
        if payload.get("iss") != "inboxradar-frontend":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer"
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signature has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid security token. Ensure NEXT_PUBLIC_API_TOKEN matches backend JWT_SECRET."
        )

def verify_websocket_token(token: str = Query(None)) -> dict:
    """Verifies the JWT token passed as a query parameter for WebSocket handshakes."""
    if not token:
        import logging
        logging.getLogger(__name__).warning("WebSocket auth failed: Token is missing.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="WebSocket authentication token is missing"
        )
        
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
        if payload.get("iss") != "inboxradar-frontend":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid WebSocket token issuer"
            )
        return payload
    except jwt.PyJWTError as e:
        import logging
        logging.getLogger(__name__).error(f"WebSocket JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid WebSocket security token"
        )
