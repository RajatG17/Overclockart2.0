import pytest
from services.auth.app.security import hash_password, verify_password, create_access_token, decode_access_token

def test_hash_and_verify_password():
    password = "StrongPassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_create_and_decode_token():
    user_id = "123456"
    token = create_access_token(user_id)
    assert isinstance(token, str)
    
    decoded = decode_access_token(token)
    assert decoded["sub"] == user_id
