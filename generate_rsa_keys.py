#!/usr/bin/env python3
"""
RSA Key Pair Generator for JWT Authentication

This script generates RSA private and public key pairs for JWT token signing.
The keys are saved to the 'certs' directory.

Usage:
    python generate_rsa_keys.py

Output:
    - certs/private.pem: RSA private key (for signing tokens)
    - certs/public.pem: RSA public key (for verifying tokens)
"""

import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


def generate_rsa_keys(key_size: int = 2048) -> tuple[str, str]:
    """
    Generate RSA private and public key pair.

    Args:
        key_size: Size of the RSA key in bits (default: 2048)

    Returns:
        Tuple of (private_key_pem, public_key_pem)
    """
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )

    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    # Extract and serialize public key
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    return private_pem, public_pem


def save_keys_to_files(private_key: str, public_key: str, output_dir: str = "certs"):
    """
    Save RSA keys to files.

    Args:
        private_key: PEM-encoded private key
        public_key: PEM-encoded public key
        output_dir: Directory to save keys (default: 'certs')
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    private_path = os.path.join(output_dir, "private.pem")
    public_path = os.path.join(output_dir, "public.pem")

    with open(private_path, "w") as f:
        f.write(private_key)

    with open(public_path, "w") as f:
        f.write(public_key)

    # Set restrictive permissions on private key
    os.chmod(private_path, 0o600)

    print(f"✅ Private key saved to: {private_path}")
    print(f"✅ Public key saved to: {public_path}")


def print_env_format(private_key: str, public_key: str):
    """
    Print keys in .env file format (for environment variables).

    Args:
        private_key: PEM-encoded private key
        public_key: PEM-encoded public key
    """
    # Convert newlines to \\n for .env format
    private_env = private_key.replace("\n", "\\n")
    public_env = public_key.replace("\n", "\\n")

    print("\n" + "=" * 60)
    print("📋 Add these to your .env file:")
    print("=" * 60)
    print(f'\nJWT_PRIVATE_KEY="{private_env}"')
    print(f'\nJWT_PUBLIC_KEY="{public_env}"')
    print("\n" + "=" * 60)


def main():
    print("🔐 Generating RSA key pair for JWT authentication...")
    print(f"   Key size: 2048 bits")
    print(f"   Algorithm: RS256\n")

    private_key, public_key = generate_rsa_keys()

    # Save to files
    save_keys_to_files(private_key, public_key)

    # Print environment variable format
    print_env_format(private_key, public_key)

    print("\n✅ RSA key generation complete!")
    print("\n⚠️  Keep your private key secure and never commit it to version control!")


if __name__ == "__main__":
    main()
