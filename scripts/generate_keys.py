#!/usr/bin/env python3
"""Script to generate JWT RSA keys."""

import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_keys(output_dir: Path = Path("keys")) -> None:
    """Generate RSA key pair for JWT signing."""
    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Write private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    private_path = output_dir / "jwtRS256.key"
    private_path.write_bytes(private_pem)
    private_path.chmod(0o600)
    print(f"✓ Private key written to: {private_path}")

    # Write public key
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    public_path = output_dir / "jwtRS256.key.pub"
    public_path.write_bytes(public_pem)
    print(f"✓ Public key written to: {public_path}")

    print("\n✓ JWT keys generated successfully!")
    print("\nUpdate your .env file with:")
    print(f"JWT_PRIVATE_KEY_PATH={private_path}")
    print(f"JWT_PUBLIC_KEY_PATH={public_path}")


if __name__ == "__main__":
    generate_keys()
