"""
Security unit tests.
Tests: password hashing, JWT, permissions.
"""
import pytest
from app.core.security import (
    hash_password, verify_password,
    create_access_token, decode_access_token,
    create_refresh_token, decode_refresh_token,
    generate_secure_filename,
)
from app.core.permissions import UserRole, Permission, has_permission, ROLE_PERMISSIONS


# ─── Password Tests ───────────────────────────────────────────────────────────

def test_password_hash_not_plaintext():
    h = hash_password("MySecurePass123")
    assert h != "MySecurePass123"
    assert len(h) > 30


def test_password_verify_correct():
    h = hash_password("TestPass@1234")
    assert verify_password("TestPass@1234", h) is True


def test_password_verify_wrong():
    h = hash_password("RealPass@1234")
    assert verify_password("WrongPass", h) is False


def test_password_different_hashes():
    """Same password produces different hashes (bcrypt salt)."""
    h1 = hash_password("SamePass")
    h2 = hash_password("SamePass")
    assert h1 != h2  # bcrypt salts
    assert verify_password("SamePass", h1)
    assert verify_password("SamePass", h2)


# ─── JWT Tests ────────────────────────────────────────────────────────────────

def test_access_token_decode():
    token = create_access_token(42, extra_claims={"role": "DEPARTMENT_OFFICIAL"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["type"] == "access"
    assert payload["role"] == "DEPARTMENT_OFFICIAL"


def test_refresh_token_decode():
    token = create_refresh_token(99)
    payload = decode_refresh_token(token)
    assert payload is not None
    assert payload["sub"] == "99"
    assert payload["type"] == "refresh"
    assert "jti" in payload


def test_access_token_wrong_type():
    """Refresh token must not be accepted as access token."""
    token = create_refresh_token(1)
    result = decode_access_token(token)
    assert result is None


def test_refresh_token_wrong_type():
    """Access token must not be accepted as refresh token."""
    token = create_access_token(1)
    result = decode_refresh_token(token)
    assert result is None


def test_invalid_token_returns_none():
    assert decode_access_token("not.a.valid.token") is None
    assert decode_refresh_token("garbage") is None


# ─── Permission Tests ─────────────────────────────────────────────────────────

def test_official_can_assign():
    assert has_permission(UserRole.DEPARTMENT_OFFICIAL, Permission.INSPECTION_ASSIGN)


def test_inspector_cannot_assign():
    assert not has_permission(UserRole.INSPECTION_OFFICER, Permission.INSPECTION_ASSIGN)


def test_inspector_cannot_make_decision():
    assert not has_permission(UserRole.INSPECTION_OFFICER, Permission.DECISION_MAKE)


def test_inspector_can_conduct():
    assert has_permission(UserRole.INSPECTION_OFFICER, Permission.INSPECTION_CONDUCT)


def test_citizen_has_minimal_permissions():
    perms = ROLE_PERMISSIONS[UserRole.CITIZEN]
    assert len(perms) <= 2


def test_project_staff_no_audit():
    assert not has_permission(UserRole.PROJECT_STAFF, Permission.AUDIT_READ)


def test_super_admin_has_all():
    for perm in Permission:
        assert has_permission(UserRole.SUPER_ADMIN, perm)


def test_pmu_no_decision():
    """PMU can review but not make final decisions."""
    # PMU can review but DECISION_MAKE is reserved for OFFICIAL
    assert not has_permission(UserRole.PMU_OFFICER, Permission.DECISION_MAKE)


# ─── File Security Tests ──────────────────────────────────────────────────────

def test_safe_filename_no_original():
    """Server-generated filename must not contain original name."""
    safe = generate_secure_filename("../../etc/passwd")
    assert "etc" not in safe
    assert "passwd" not in safe
    assert len(safe) > 10


def test_safe_filename_preserves_extension():
    safe = generate_secure_filename("photo.jpg")
    assert safe.endswith(".jpg")


def test_safe_filename_unique():
    f1 = generate_secure_filename("test.jpg")
    f2 = generate_secure_filename("test.jpg")
    assert f1 != f2
