import hashlib
import time


def cpu_lag(ticks: int, seed: bytes = b'heart-api-lag') -> None:
    value = seed
    for _ in range(ticks):
        value = hashlib.sha256(value).digest()
    _ = value.hex()


def cpu_lag_until(deadline: float) -> None:
    while time.time() < deadline:
        cpu_lag(10000)
