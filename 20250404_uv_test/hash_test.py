def simple_hash(text, hash_size=1024):
    hash_value = 0
    for char in text:
        # 文字のASCIIコードを取得して計算
        hash_value = (hash_value * 31 + ord(char)) % hash_size
    return hash_value

# 使用例
print(simple_hash("Hello"))
print(simple_hash("World"))
print(simple_hash("Hello World"))
print(simple_hash("Hello"))



def custom_hash(text, hash_size=65536):
    hash_value = 0xABCDEF
    for char in text:
        hash_value ^= ord(char)
        hash_value = (hash_value << 5) | (hash_value >> 27)  # ビットローテーション
        hash_value &= 0xFFFFFFFF  # 32ビットに制限
    return hash_value % hash_size

# 使用例
print(custom_hash("Hello"))
print(custom_hash("World"))
print(custom_hash("Hello World"))


from cryptography.fernet import Fernet

# 暗号化キー生成
key = Fernet.generate_key()
cipher = Fernet(key)

# 暗号化
encrypted = cipher.encrypt(b"Hello World")
print(encrypted)

# 復号（元に戻す）
decrypted = cipher.decrypt(encrypted)
print(decrypted.decode())