"""Tests de manejo de fallos de red: reintentos, backoff y timeout -- sin red real."""

from __future__ import annotations

import unittest
import urllib.error

from services.collector.http_client import FetchError, RetryPolicy, fetch_with_retry


class RetrySuccessAfterFailuresTests(unittest.TestCase):
    def test_succeeds_after_two_timeouts(self) -> None:
        calls: list[str] = []

        def flaky_fetcher(url: str, timeout: float) -> bytes:
            calls.append(url)
            if len(calls) < 3:
                raise TimeoutError("simulated timeout")
            return b'{"ok": true}'

        sleeps: list[float] = []
        policy = RetryPolicy(max_retries=3, backoff_base_seconds=1.0, timeout_seconds=5.0)

        result = fetch_with_retry(
            "https://example.invalid/feed.json",
            policy,
            fetcher=flaky_fetcher,
            sleep=sleeps.append,
        )

        self.assertEqual(result, b'{"ok": true}')
        self.assertEqual(len(calls), 3)
        # Backoff exponencial: 1*2^0, 1*2^1 entre los dos primeros fallos y el éxito.
        self.assertEqual(sleeps, [1.0, 2.0])


class RetryExhaustionTests(unittest.TestCase):
    def test_raises_fetch_error_after_exhausting_retries(self) -> None:
        def always_fails(url: str, timeout: float) -> bytes:
            raise urllib.error.URLError("simulated network error")

        sleeps: list[float] = []
        policy = RetryPolicy(max_retries=2, backoff_base_seconds=0.5, timeout_seconds=5.0)

        with self.assertRaises(FetchError):
            fetch_with_retry(
                "https://example.invalid/feed.json",
                policy,
                fetcher=always_fails,
                sleep=sleeps.append,
            )

        # 3 intentos totales (1 inicial + 2 reintentos), 2 esperas entre ellos,
        # ninguna espera tras el último intento fallido.
        self.assertEqual(sleeps, [0.5, 1.0])

    def test_does_not_retry_on_non_network_exception(self) -> None:
        def raises_value_error(url: str, timeout: float) -> bytes:
            raise ValueError("esto no es un error de red, no debe reintentarse")

        policy = RetryPolicy(max_retries=3, backoff_base_seconds=0.1, timeout_seconds=5.0)

        with self.assertRaises(ValueError):
            fetch_with_retry(
                "https://example.invalid/feed.json",
                policy,
                fetcher=raises_value_error,
                sleep=lambda _: None,
            )


class RetryTimeoutParameterTests(unittest.TestCase):
    def test_timeout_seconds_is_passed_to_fetcher(self) -> None:
        received_timeouts: list[float] = []

        def recording_fetcher(url: str, timeout: float) -> bytes:
            received_timeouts.append(timeout)
            return b"{}"

        policy = RetryPolicy(max_retries=0, backoff_base_seconds=0.1, timeout_seconds=7.5)
        fetch_with_retry(
            "https://example.invalid/feed.json", policy, fetcher=recording_fetcher
        )

        self.assertEqual(received_timeouts, [7.5])


if __name__ == "__main__":
    unittest.main()
