# backend/tests/test_load.py
"""
Locust load test for the AI Agentic Assistant V2.
Tests WebSocket chat + REST API endpoints under concurrent load.

Run:
  pip install locust
  locust -f backend/tests/test_load.py --host=http://localhost:8000 \
         --users=50 --spawn-rate=5 --run-time=5m --headless

Targets:
  - 50 concurrent users
  - p95 response time < 8s
  - Error rate < 2%
  - WebSocket: 10 parallel streaming sessions
"""
import json
import random
import time
import threading

# Skip this file when locust is not installed so pytest can still collect
# the rest of the test suite.  Install locust separately to run load tests:
#   pip install locust websocket-client
import pytest
pytest.importorskip("locust")

from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import websocket   # pip install websocket-client


TEST_QUERIES = [
    "What is Retrieval Augmented Generation?",
    "Explain the difference between FAISS and ChromaDB",
    "Write a Python function to compute cosine similarity",
    "What is LangGraph and how does it work?",
    "List the key benefits of multi-agent AI systems",
    "How does HyDE improve RAG retrieval accuracy?",
    "What is the Reflexion pattern in AI agents?",
    "Explain prompt injection attacks and how to prevent them",
    "What are the tradeoffs between GPT-4o and open-source models?",
    "Describe vector database indexing strategies",
]

HEADERS = {"Authorization": "Bearer dev"}


class RestAPIUser(FastHttpUser):
    """Tests REST API endpoints."""
    wait_time = between(1, 4)

    @task(3)
    def health_check(self):
        with self.client.get("/api/health", headers=HEADERS, catch_response=True) as r:
            if r.status_code == 200:
                data = r.json()
                if data.get("status") != "ok":
                    r.failure(f"Health check degraded: {data}")
            else:
                r.failure(f"Health check failed: {r.status_code}")

    @task(2)
    def rag_stats(self):
        self.client.get("/api/rag/stats", headers=HEADERS)

    @task(2)
    def cost_report(self):
        self.client.get("/api/cost/report?days=7", headers=HEADERS)

    @task(1)
    def classify_query(self):
        query = random.choice(TEST_QUERIES)
        self.client.post(
            f"/api/cost/classify?query={query[:80]}",
            headers=HEADERS,
        )

    @task(1)
    def llm_health(self):
        self.client.get("/api/llm/health", headers=HEADERS)

    @task(1)
    def memory_fetch(self):
        self.client.get("/api/memory/dev-user-001?limit=10", headers=HEADERS)

    @task(1)
    def mcp_tools_list(self):
        self.client.get("/mcp/tools", headers=HEADERS)


class WebSocketUser(HttpUser):
    """Tests WebSocket streaming chat."""
    wait_time = between(5, 15)   # longer wait — WS sessions are expensive

    def on_start(self):
        """Called once per user when they start."""
        self.ws_url = self.host.replace("http://", "ws://") + "/ws"
        self.session_id = f"load-test-{random.randint(1000, 9999)}"

    @task
    def chat_via_websocket(self):
        """
        Full WebSocket chat session:
        connect → send message → receive tokens → receive done → disconnect
        """
        query      = random.choice(TEST_QUERIES)
        url        = f"{self.ws_url}?session_id={self.session_id}"
        start_time = time.time()
        token_count = 0
        error_msg   = None
        done        = False

        try:
            ws = websocket.create_connection(url, timeout=60)

            # Send query
            ws.send(json.dumps({
                "type":       "text",
                "content":    query,
                "session_id": self.session_id,
                "user_id":    "load-test-user",
            }))

            # Receive tokens until done or error
            while not done:
                raw  = ws.recv()
                if not raw:
                    break
                msg = json.loads(raw)

                if msg["type"] == "token":
                    token_count += 1
                elif msg["type"] == "done":
                    done = True
                elif msg["type"] == "error":
                    error_msg = msg.get("message", "unknown error")
                    break
                elif msg["type"] in ("agent_step", "guard_event", "pong"):
                    continue  # expected — no action needed

            ws.close()

        except Exception as e:
            error_msg = str(e)

        elapsed_ms = int((time.time() - start_time) * 1000)

        # Report to Locust metrics
        events.request.fire(
            request_type="WebSocket",
            name="/ws chat",
            response_time=elapsed_ms,
            response_length=token_count,
            exception=Exception(error_msg) if error_msg else None,
        )

    @task(2)
    def ping_websocket(self):
        """Lightweight WS ping test."""
        url = f"{self.ws_url}?session_id=ping-{random.randint(1, 999)}"
        try:
            ws = websocket.create_connection(url, timeout=10)
            ws.send(json.dumps({"type": "ping"}))
            raw = ws.recv()
            msg = json.loads(raw)
            ws.close()
            ok  = msg.get("type") == "pong"
            events.request.fire(
                request_type="WebSocket",
                name="/ws ping",
                response_time=50,
                response_length=1,
                exception=None if ok else Exception("No pong"),
            )
        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="/ws ping",
                response_time=10000,
                response_length=0,
                exception=e,
            )