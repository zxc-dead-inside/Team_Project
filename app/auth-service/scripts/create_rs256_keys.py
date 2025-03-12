"""
Script to create a public and private keys for JWT with algorithm RS256.
"""

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import os
from pathlib import Path


def create_keys_pair(keys_dir: str ='secrets', key_size: int =2048, overwrite: bool =False):
    """
    Create RSA key pair for JWT authentication.
    
    Args:
        keys_dir (str): Directory to store the keys
        key_size (int): Size of RSA key in bits
        overwrite (bool): Whether to overwrite existing keys
    
    Returns:
        tuple: Paths to the created private and public key files
    """

    keys_dir: Path = Path(keys_dir)
    private_key_path = keys_dir.joinpath("private_key.pem")
    public_key_path = keys_dir.joinpath("public_key.pem")

    # Create directory if it doesn't exist
    keys_dir.mkdir(exist_ok=True)

    if not overwrite and private_key_path.exists() and public_key_path.exists():
        return private_key_path, public_key_path
    
    # Генерация закрытого ключа RSA длиной 2048 бит
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )

    # Генерация открытого ключа
    public_key = private_key.public_key()

    # Сериализация закрытого ключа в PEM формат
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Сериализация открытого ключа в PEM формат
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Сохранение ключей в файлы
    with open(private_key_path, "wb") as private_file:
        private_file.write(private_pem)
    with open(public_key_path, "wb") as public_file:
        public_file.write(public_pem)
    
    return private_key_path, public_key_path

def main():
    """Main function to run script."""
    create_keys_pair()

if __name__ == "__main__":
    main()
