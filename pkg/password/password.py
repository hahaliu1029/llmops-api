# 密码校验正则，密码最少包含一个字母、一个数字，并且长度在8-16
import binascii
import base64
import re
from typing import Any
import hashlib


password_pattern = r"^(?=.*[A-Za-z])(?=.*\d).{8,16}$"


def validate_password(password: str, pattern: str = password_pattern):
    """根据正则校验密码"""
    if re.match(pattern, password) is None:
        raise ValueError(
            "密码不符合规范, 密码最少包含一个字母、一个数字，并且长度在8-16"
        )
    return


def hash_password(password: str, salt: Any) -> bytes:
    """将传入的密码+盐值进行哈希加密"""
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 10000)
    return binascii.hexlify(dk)


def compare_password(
    password: str, password_hashed_base64: Any, salt_base64: Any
) -> bool:
    """比较密码和哈希值"""
    return hash_password(password, base64.b64decode(salt_base64)) == base64.b64decode(
        password_hashed_base64
    )
