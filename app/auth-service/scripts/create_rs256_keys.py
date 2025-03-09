"""
Script to create a public and private keys for JWT with algorithm RS256.
"""

import asyncio
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import os


async def create_keys_pair():

    keys_dir = 'secrets'

    if not os.path.exists(keys_dir):
        os.makedirs(keys_dir)

    # Генерация закрытого ключа RSA длиной 2048 бит
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
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

    # Путь для сохранения ключей
    private_key_path = os.path.join(keys_dir, "private_key.pem")
    public_key_path = os.path.join(keys_dir, "public_key.pem")

    # Сохранение ключей в файлы
    with open(private_key_path, "wb") as private_file:
        private_file.write(private_pem)

    with open(public_key_path, "wb") as public_file:
        public_file.write(public_pem)

    return None


def main():
    """Main function to run script."""
    asyncio.run(create_keys_pair())



if __name__ == "__main__":
    main()
