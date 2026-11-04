from cryptography.fernet import Fernet
open("key.bin", "wb").write(Fernet.generate_key())