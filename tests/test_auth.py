from core.auth import generate_api_key, verify_api_key


def test_generate_api_key_format():
    key = generate_api_key()
    assert key.startswith("nvc_")
    assert len(key) == 4 + 48  # prefix + 24 bytes as hex


def test_generate_api_key_unique():
    k1 = generate_api_key()
    k2 = generate_api_key()
    assert k1 != k2


def test_verify_api_key_correct():
    key = generate_api_key()
    assert verify_api_key(key, key) is True


def test_verify_api_key_wrong():
    k1 = generate_api_key()
    k2 = generate_api_key()
    assert verify_api_key(k1, k2) is False


def test_verify_api_key_empty():
    key = generate_api_key()
    assert verify_api_key("", key) is False
    assert verify_api_key(key, "") is False
    assert verify_api_key("", "") is False
