from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt

# ⚠️ Change this to a long random string in production!
SECRET_KEY = "your-super-secret-key-change-this"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60  # Token valid for 1 hour


# --- Verify a plain password against the stored hash ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode(),
        hashed_password.encode()
    )


# --- Create a JWT token for a logged-in employee ---
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --- Decode and verify a JWT token ---
def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None