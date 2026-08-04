import pytest
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


class TestPasswordHashing:
	def test_hash_is_not_plaintext(self):
		hashed = hash_password("mypassword")
		assert hashed != "mypassword"
		assert len(hashed) > 20

	def test_correct_password_verifies(self):
		hashed = hash_password("correct")
		assert verify_password("correct", hashed) is True

	def test_wrong_password_fails(self):
		hashed = hash_password("correct")
		assert verify_password("wrong", hashed) is False

	def test_different_hashes_for_same_password(self):
		h1 = hash_password("same")
		h2 = hash_password("same")
		assert h1 != h2


class TestJWT:
	def test_token_contains_subject(self):
		token = create_access_token(subject="42", role="student")
		payload = decode_access_token(token)
		assert payload["sub"] == "42"
		assert payload["role"] == "student"

	def test_invalid_token_raises(self):
		from fastapi import HTTPException

		with pytest.raises(HTTPException) as exc:
			decode_access_token("invalid.jwt.token")
		assert exc.value.status_code == 401
