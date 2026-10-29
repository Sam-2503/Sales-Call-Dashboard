from starlette.requests import Request

from analyser_api.auth.ratelimit import RateLimiter, client_ip


def test_fixed_window_limiter_rejects_the_third_request() -> None:
    limiter = RateLimiter(2, 3600)
    assert limiter.allow("a") is True
    assert limiter.allow("a") is True
    assert limiter.allow("a") is False
    assert limiter.allow("b") is True
    assert limiter.retry_after("a") > 0


def test_client_ip_uses_only_the_trusted_hop() -> None:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"x-forwarded-for", b"spoofed, client, proxy")],
        "client": ("10.0.0.1", 1234),
    }
    request = Request(scope)
    assert client_ip(request, 1) == "proxy"
    assert client_ip(request, 2) == "client"
    assert client_ip(request, 0) == "10.0.0.1"
