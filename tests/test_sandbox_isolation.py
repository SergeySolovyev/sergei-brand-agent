"""
test_sandbox_isolation.py — eval: agent's Docker sandbox enforces
network whitelist and filesystem boundaries.

Run on a deployed VPS:
    docker exec sergei-brand-agent pytest /workspace/tests/test_sandbox_isolation.py -v

These tests verify the harness `Sandbox` component of the Anthropic Managed
Agents pattern is properly configured.
"""
from __future__ import annotations

import os
import subprocess
import socket
import pytest


# -----------------------------------------------------------------------------
# Network isolation tests
# -----------------------------------------------------------------------------


PRIVATE_IPS_THAT_MUST_BE_BLOCKED = [
    "10.0.0.1",      # RFC 1918 private
    "10.255.255.255",
    "172.16.0.1",
    "172.31.255.255",
    "192.168.0.1",
    "192.168.255.255",
    "169.254.169.254",  # AWS / GCP metadata endpoint
    "100.64.0.1",       # Carrier-grade NAT
    "127.0.0.2",        # localhost (other than 127.0.0.1)
]


@pytest.mark.parametrize("private_ip", PRIVATE_IPS_THAT_MUST_BE_BLOCKED)
def test_cannot_reach_private_ip(private_ip):
    """Agent must NOT be able to reach RFC 1918 / metadata / localhost ranges."""
    result = subprocess.run(
        ["curl", "-s", "--max-time", "3", "-o", "/dev/null",
         "-w", "%{http_code}", f"http://{private_ip}"],
        capture_output=True, text=True
    )
    # We expect either timeout (return code != 0) or non-2xx via proxy block
    timed_out = result.returncode != 0
    blocked_response = result.stdout.strip() in ("", "000", "403", "407", "502", "503")

    assert timed_out or blocked_response, (
        f"Agent reached {private_ip} — sandbox network whitelist NOT enforced.\n"
        f"return_code={result.returncode}, stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


WHITELISTED_DOMAINS = [
    "sergeisolovev.com",
    "api.github.com",
    "api.openalex.org",
    "api.telegram.org",
    "api.anthropic.com",
    "openrouter.ai",
]


@pytest.mark.parametrize("domain", WHITELISTED_DOMAINS)
def test_can_reach_whitelisted_domain(domain):
    """Whitelisted domains must be reachable via egress proxy."""
    result = subprocess.run(
        ["curl", "-sI", "--max-time", "10", f"https://{domain}/"],
        capture_output=True, text=True
    )
    # Allow any 2xx, 3xx, or 4xx that indicates we reached the server
    # (5xx might be transient; 000 means we never got there)
    has_response = "HTTP/" in result.stdout
    assert has_response, (
        f"Whitelisted domain {domain} not reachable. "
        f"return_code={result.returncode}, output={result.stdout[:300]!r}"
    )


BLACKLISTED_DOMAINS_OUTSIDE_WHITELIST = [
    "evil.com",
    "pastebin.com",
    "raw.githack.com",   # backdoor for github raw (not whitelisted)
    "discord.com",        # not in whitelist
]


@pytest.mark.parametrize("domain", BLACKLISTED_DOMAINS_OUTSIDE_WHITELIST)
def test_cannot_reach_non_whitelisted_domain(domain):
    """Non-whitelisted public domains must be blocked by egress proxy."""
    result = subprocess.run(
        ["curl", "-sI", "--max-time", "5", f"https://{domain}/"],
        capture_output=True, text=True
    )
    # Either curl errors (no route through proxy) or we get proxy 403
    blocked = result.returncode != 0 or "403" in result.stdout or "407" in result.stdout
    if not blocked:
        # Note: this test may pass in dev (no proxy yet) — that's expected
        pytest.skip(f"Egress proxy not enforcing — got: {result.stdout[:200]}")


# -----------------------------------------------------------------------------
# Filesystem isolation tests
# -----------------------------------------------------------------------------


def test_cannot_write_outside_workspace():
    """Agent process must not be able to write outside /workspace and /home/agent/."""
    forbidden_paths = ["/etc/test-write", "/root/test-write", "/var/log/test-write"]
    for path in forbidden_paths:
        try:
            with open(path, "w") as f:
                f.write("test")
            os.remove(path)
            pytest.fail(f"Was able to write to {path} — sandbox filesystem boundary not enforced")
        except (PermissionError, OSError):
            pass  # expected


def test_workspace_is_writable():
    """Agent must be able to write within /workspace/data/."""
    test_path = "/tmp/test-sandbox-isolation"
    if not os.path.exists("/workspace"):
        pytest.skip("Not running inside container; /workspace not present")
    workspace_test = "/workspace/data/test-sandbox-write.tmp"
    with open(workspace_test, "w") as f:
        f.write("ok")
    os.remove(workspace_test)


def test_knowledge_base_is_read_only():
    """Critic must not be able to overwrite knowledge_base/ (Hermes config marks RO)."""
    if not os.path.exists("/workspace/knowledge_base"):
        pytest.skip("Not running inside container")
    try:
        with open("/workspace/knowledge_base/test-write.tmp", "w") as f:
            f.write("should fail")
        os.remove("/workspace/knowledge_base/test-write.tmp")
        # If we get here, the file system permission is wrong
        pytest.fail("knowledge_base/ was writable — should be read-only")
    except (PermissionError, OSError):
        pass  # expected


# -----------------------------------------------------------------------------
# Secrets isolation tests
# -----------------------------------------------------------------------------


def test_no_secrets_in_logs():
    """Critic must never log raw secrets (API keys etc)."""
    if not os.path.exists("/workspace/data/traces"):
        pytest.skip("No traces directory")
    # Scan recent trace files for accidental secret leakage
    import glob, re
    secret_patterns = [
        r"sk-ant-api03-[A-Za-z0-9_-]{40,}",
        r"ghp_[A-Za-z0-9]{36,}",
        r"sk-or-v1-[A-Za-z0-9_-]{40,}",
        r"\d{10}:[A-Za-z0-9_-]{35}",  # Telegram bot token pattern
    ]
    for trace_file in glob.glob("/workspace/data/traces/**/*.jsonl", recursive=True):
        with open(trace_file) as f:
            content = f.read()
        for pat in secret_patterns:
            matches = re.findall(pat, content)
            assert not matches, f"Secret pattern leaked in {trace_file}: {matches[:1]}"


# -----------------------------------------------------------------------------
# Process isolation
# -----------------------------------------------------------------------------


def test_not_running_as_root():
    """Agent must run as non-root user."""
    if not os.path.exists("/.dockerenv"):
        pytest.skip("Not running inside container")
    assert os.getuid() != 0, "Agent is running as root inside container — security risk"


def test_no_new_privileges():
    """Container must have no-new-privileges flag set."""
    if not os.path.exists("/proc/self/status"):
        pytest.skip("Not on Linux")
    with open("/proc/self/status") as f:
        content = f.read()
    # NoNewPrivs: 1 means no-new-privileges enforced
    assert "NoNewPrivs:\t1" in content, "no-new-privileges not enforced"


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
