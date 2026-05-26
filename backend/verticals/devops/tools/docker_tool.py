# backend/verticals/devops/tools/docker_tool.py
"""
Docker log retrieval tool.
Fetches container logs from the local Docker daemon.
Runs safely — read-only operations only.
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

MAX_LOG_LINES = 200


async def get_container_logs(
    container_name: str,
    tail:           int = 100,
    since_minutes:  int = 60,
) -> dict:
    """
    Fetch recent logs from a Docker container.
    Uses docker logs CLI — works without Python docker SDK.
    """
    since = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
    since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "logs",
            "--tail",  str(min(tail, MAX_LOG_LINES)),
            "--since", since_str,
            "--timestamps",
            container_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15.0)
        logs = (stdout + stderr).decode("utf-8", errors="replace")

        # Extract errors and warnings
        lines      = logs.splitlines()
        errors     = [l for l in lines if any(w in l.lower() for w in ["error", "fatal", "exception", "panic"])]
        warnings   = [l for l in lines if "warn" in l.lower()]

        return {
            "container": container_name,
            "log_lines": len(lines),
            "errors":    errors[:20],
            "warnings":  warnings[:10],
            "recent_logs": "\n".join(lines[-50:]),
            "since_minutes": since_minutes,
        }
    except asyncio.TimeoutError:
        return {"container": container_name, "error": "Docker logs timed out"}
    except Exception as e:
        return {"container": container_name, "error": str(e)}


async def list_containers(only_running: bool = True) -> list[dict]:
    """List Docker containers."""
    try:
        args = ["docker", "ps", "--format",
                "{{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}"]
        if not only_running:
            args.append("-a")

        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10.0)
        lines     = stdout.decode().strip().splitlines()

        containers = []
        for line in lines:
            parts = line.split("\t")
            if len(parts) >= 3:
                containers.append({
                    "name":   parts[0],
                    "status": parts[1],
                    "image":  parts[2],
                    "ports":  parts[3] if len(parts) > 3 else "",
                })
        return containers
    except Exception as e:
        logger.error(f"Docker list failed: {e}")
        return []


async def get_container_stats(container_name: str) -> dict:
    """Get container resource usage (CPU, memory)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "stats", "--no-stream", "--format",
            "{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}",
            container_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10.0)
        parts     = stdout.decode().strip().split("\t")

        if len(parts) >= 2:
            return {
                "container": container_name,
                "cpu_pct":   parts[0],
                "memory":    parts[1],
                "network":   parts[2] if len(parts) > 2 else "n/a",
                "disk_io":   parts[3] if len(parts) > 3 else "n/a",
            }
        return {"container": container_name, "error": "No stats returned"}
    except Exception as e:
        return {"container": container_name, "error": str(e)}