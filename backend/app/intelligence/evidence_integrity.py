"""
Evidence Integrity Engine
==========================
SHA-256 hash generation and verification for uploaded evidence files.

This verifies byte-level consistency — it confirms the file has not been
modified since upload. It does NOT verify the truthfulness of the scene depicted.
"""
import hashlib
import os
from pathlib import Path


def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file. Reads in 64KB chunks for memory efficiency."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_sha256_bytes(data: bytes) -> str:
    """Compute SHA-256 hash of bytes in memory."""
    return hashlib.sha256(data).hexdigest()


def verify_evidence_integrity(
    file_path: str,
    stored_hash: str,
) -> dict:
    """
    Verify evidence file integrity by comparing current hash to stored hash.

    Returns:
      result: VERIFIED / MISMATCH / ERROR
      computed_hash: current hash
      stored_hash: original stored hash
      match: bool
      note: human-readable explanation
    """
    try:
        if not os.path.exists(file_path):
            return {
                "result": "ERROR",
                "computed_hash": "",
                "stored_hash": stored_hash,
                "match": False,
                "note": "Evidence file not found on server",
            }

        current_hash = compute_sha256(file_path)
        match = current_hash.lower() == stored_hash.lower()

        return {
            "result": "VERIFIED" if match else "MISMATCH",
            "computed_hash": current_hash,
            "stored_hash": stored_hash,
            "match": match,
            "note": (
                "File bytes match stored fingerprint. "
                "File has not been modified since upload."
                if match
                else
                "Hash mismatch detected. File may have been modified since upload."
            ),
            "algorithm": "SHA-256",
            "disclaimer": (
                "Hash verification confirms byte-level consistency. "
                "It does not verify the authenticity of the scene depicted."
            ),
        }
    except Exception as e:
        return {
            "result": "ERROR",
            "computed_hash": "",
            "stored_hash": stored_hash,
            "match": False,
            "note": f"Verification error: {str(e)}",
        }
