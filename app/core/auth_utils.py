import hashlib
import os

# Parameters for PBKDF2
# Iterations should be as high as your system can tolerate. OWASP recommends at least 100,000 for PBKDF2-SHA256.
# For demonstration, using a slightly lower number, but increase for production.
ITERATIONS = 150000
SALT_SIZE_BYTES = 16  # 16 bytes = 128 bits, a common size for salt
HASH_ALGORITHM = 'sha256' # Algorithm to use with PBKDF2

def generate_salt_hex() -> str:
    """
    Generates a cryptographically secure random salt and returns it as a hex string.
    """
    return os.urandom(SALT_SIZE_BYTES).hex()

def hash_password(password: str, salt_hex: str) -> str:
    """
    Hashes a password using PBKDF2 with the given salt (hex string).
    Returns the hash as a hex string.
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string.")
    if not isinstance(salt_hex, str):
        raise TypeError("Salt must be a hex string.")

    try:
        salt_bytes = bytes.fromhex(salt_hex)
    except ValueError:
        raise ValueError("Invalid hex string for salt.")

    if len(salt_bytes) != SALT_SIZE_BYTES:
        raise ValueError(f"Salt must be {SALT_SIZE_BYTES} bytes long (or {SALT_SIZE_BYTES*2} hex chars).")

    password_bytes = password.encode('utf-8')

    # PBKDF2 (Password-Based Key Derivation Function 2)
    # dklen=None means the digest size of the hash algorithm is used (e.g., 32 bytes for SHA256)
    hashed_bytes = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        password_bytes,
        salt_bytes,
        ITERATIONS,
        dklen=None
    )
    return hashed_bytes.hex()

def verify_password(stored_password_hash_hex: str, salt_hex: str, provided_password: str) -> bool:
    """
    Verifies a provided password against a stored hash and salt.
    All inputs (hash, salt) are expected as hex strings.
    """
    if not isinstance(provided_password, str):
        # Or handle more gracefully depending on application context
        print("Warning: Provided password for verification was not a string.")
        return False

    try:
        # Hash the provided password with the same salt and iterations
        new_hash_hex = hash_password(provided_password, salt_hex)
        # Compare the new hash with the stored hash using a constant-time comparison
        # to prevent timing attacks (though for server-side, direct comparison is often acceptable).
        # Python's `==` for strings is generally optimized but not strictly constant-time.
        # For higher security needs, `hmac.compare_digest` is preferred.
        # For this application's context, direct string comparison is likely sufficient.
        return new_hash_hex == stored_password_hash_hex
    except (TypeError, ValueError) as e:
        # This can happen if salt_hex or stored_password_hash_hex are malformed
        print(f"Error during password verification pre-check (e.g. bad salt format): {e}")
        return False
    except Exception as e_gen: # Catch any other unexpected error during hashing
        print(f"Unexpected error during password verification: {e_gen}")
        return False


if __name__ == '__main__':
    print("Testing Password Hashing Utilities...")

    # Test salt generation
    salt1 = generate_salt_hex()
    salt2 = generate_salt_hex()
    print(f"Generated Salt 1 (hex): {salt1} (Length: {len(salt1)} chars)")
    print(f"Generated Salt 2 (hex): {salt2} (Length: {len(salt2)} chars)")
    assert salt1 != salt2
    assert len(salt1) == SALT_SIZE_BYTES * 2

    # Test password hashing
    password = "MySecurePassword123!"

    print(f"\nOriginal Password: {password}")

    hashed_pw1_salt1 = hash_password(password, salt1)
    print(f"Hashed with Salt 1: {hashed_pw1_salt1}")

    hashed_pw1_salt2 = hash_password(password, salt2)
    print(f"Hashed with Salt 2: {hashed_pw1_salt2}")
    assert hashed_pw1_salt1 != hashed_pw1_salt2 # Same password, different salt -> different hash

    # Test verification
    print("\nVerifying correct password with Salt 1...")
    is_verified = verify_password(hashed_pw1_salt1, salt1, password)
    print(f"Verification result: {is_verified}")
    assert is_verified is True

    print("\nVerifying incorrect password ('WrongPassword') with Salt 1...")
    is_verified_wrong_pw = verify_password(hashed_pw1_salt1, salt1, "WrongPassword")
    print(f"Verification result (wrong pw): {is_verified_wrong_pw}")
    assert is_verified_wrong_pw is False

    print("\nVerifying correct password with incorrect salt (Salt 2)...")
    is_verified_wrong_salt = verify_password(hashed_pw1_salt1, salt2, password)
    print(f"Verification result (wrong salt): {is_verified_wrong_salt}")
    assert is_verified_wrong_salt is False

    print("\nTesting with empty password (should still hash and verify if allowed by app policy)")
    empty_password = ""
    empty_pw_hash = hash_password(empty_password, salt1)
    print(f"Hashed empty password with Salt 1: {empty_pw_hash}")
    is_empty_verified = verify_password(empty_pw_hash, salt1, empty_password)
    print(f"Verification of empty password: {is_empty_verified}")
    assert is_empty_verified is True

    print("\nTesting malformed salt for hash_password (ValueError expected):")
    try:
        hash_password(password, "not-hex")
    except ValueError as e:
        print(f"Caught expected error: {e}")

    print("\nTesting malformed salt for verify_password (should return False):")
    result_malformed_salt = verify_password(hashed_pw1_salt1, "not-hex-either", password)
    print(f"Verification with malformed salt: {result_malformed_salt}")
    assert result_malformed_salt is False

    print("\nAll basic tests for auth_utils passed.")
