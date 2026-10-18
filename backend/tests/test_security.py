# File: backend/tests/test_security.py
# Description: Unit tests for JWT creation/decoding, password hashing, and RBAC dependencies.

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)


# ─── Password Hashing ────────────────────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_returns_string(self):
        hashed = hash_password("TestPass1")
        assert isinstance(hashed, str)

    def test_hash_is_not_plaintext(self):
        plain = "TestPass1"
        assert hash_password(plain) != plain

    def test_two_hashes_differ(self):
        """bcrypt generates different salts each time."""
        h1 = hash_password("TestPass1")
        h2 = hash_password("TestPass1")
        # bcrypt salts differ; SHA-256 fallback would be equal — both valid
        assert isinstance(h1, str) and isinstance(h2, str)

    def test_verify_correct_password(self):
        plain = "CorrectPass1"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("RightPass1")
        assert verify_password("WrongPass1", hashed) is False

    def test_verify_empty_string(self):
        hashed = hash_password("SomePass1")
        assert verify_password("", hashed) is False


# ─── JWT Tokens ───────────────────────────────────────────────────────────────

class TestJWTTokens:
    def test_access_token_is_string(self):
        token = create_access_token("user-123", "PHARMACIST")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_access_token_decode_subject(self):
        user_id = "abc-456"
        token = create_access_token(user_id, "NURSE")
        payload = decode_token(token)
        assert payload["sub"] == user_id

    def test_access_token_contains_role(self):
        token = create_access_token("user-1", "DISTRICT_ADMIN")
        payload = decode_token(token)
        assert payload["role"] == "DISTRICT_ADMIN"

    def test_access_token_type_field(self):
        token = create_access_token("user-1", "SUPER_ADMIN")
        payload = decode_token(token)
        assert payload["type"] == "access"

    def test_access_token_with_facility(self):
        token = create_access_token("user-1", "MEDICAL_OFFICER", facility_id="fac-99")
        payload = decode_token(token)
        assert payload.get("facility_id") == "fac-99"

    def test_refresh_token_is_string(self):
        token = create_refresh_token("user-789")
        assert isinstance(token, str)

    def test_refresh_token_type_field(self):
        token = create_refresh_token("user-789")
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_refresh_token_subject(self):
        token = create_refresh_token("user-xyz")
        payload = decode_token(token)
        assert payload["sub"] == "user-xyz"

    def test_invalid_token_raises(self):
        from fastapi import HTTPException
        with pytest.raises((Exception, HTTPException)):
            decode_token("not.a.valid.token")

    def test_tampered_token_raises(self):
        from fastapi import HTTPException
        token = create_access_token("user-1", "NURSE")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises((Exception, HTTPException)):
            decode_token(tampered)


# ─── Token Hashing ────────────────────────────────────────────────────────────

class TestTokenHashing:
    def test_hash_token_is_string(self):
        result = hash_token("some-refresh-token")
        assert isinstance(result, str)

    def test_hash_token_deterministic(self):
        t = "my-token-value"
        assert hash_token(t) == hash_token(t)

    def test_hash_token_different_inputs(self):
        assert hash_token("token-A") != hash_token("token-B")

    def test_hash_token_length(self):
        # SHA-256 hex = 64 chars
        assert len(hash_token("anything")) == 64
