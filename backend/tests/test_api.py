import tempfile
import unittest
from pathlib import Path

import httpx

from app.application import create_app
from app.core.config import Settings


class InvestigationAPITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        settings = Settings(data_directory=Path(self.temporary_directory.name))
        self.app = create_app(settings)
        self.lifespan_context = self.app.router.lifespan_context(self.app)
        await self.lifespan_context.__aenter__()
        transport = httpx.ASGITransport(app=self.app)
        self.client = httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000")
        self.csrf_token = (await self.client.get("/api/v1/csrf")).json()["token"]

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        await self.lifespan_context.__aexit__(None, None, None)
        self.temporary_directory.cleanup()

    def _mutation_headers(self, key: str = "api-test-key") -> dict[str, str]:
        return {
            "Idempotency-Key": key,
            "Origin": "http://127.0.0.1:3000",
            "Sec-Fetch-Site": "same-origin",
            "X-CSRF-Token": self.csrf_token,
        }

    async def test_create_and_detail_return_the_original_report(self) -> None:
        report = "A synthetic report survives reload."
        response = await self.client.post(
            "/api/v1/investigations",
            headers=self._mutation_headers(),
            json={"fixture_id": "discount-calculator", "report": report},
        )

        self.assertEqual(response.status_code, 202)
        detail = await self.client.get(f"/api/v1/investigations/{response.json()['id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["report"], report)
        self.assertEqual(detail.json()["verification_outcome"], "not_run")
        source_reference = next(item for item in detail.json()["evidence"] if item["kind"] == "source_reference")
        self.assertEqual(source_reference["source_ref"]["path"], "fixtures/discount_calculator/calculator.py")
        replay = await self.client.post(
            "/api/v1/investigations",
            headers=self._mutation_headers(),
            json={"fixture_id": "discount-calculator", "report": report},
        )
        self.assertEqual(replay.status_code, 202)
        self.assertEqual(replay.json()["id"], response.json()["id"])
        self.assertEqual(
            set(replay.json()),
            {"id", "status", "verification_outcome", "execution_status", "provider_mode"},
        )

    async def test_mutation_without_valid_browser_security_headers_is_rejected(self) -> None:
        response = await self.client.post(
            "/api/v1/investigations",
            headers={"Idempotency-Key": "missing-csrf"},
            json={"fixture_id": "discount-calculator", "report": "A report"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "invalid_request")
        self.assertIn("request_id", response.json())

    async def test_report_and_json_body_limits_are_enforced(self) -> None:
        report_response = await self.client.post(
            "/api/v1/investigations",
            headers=self._mutation_headers("large-report"),
            json={"fixture_id": "discount-calculator", "report": "x" * (16 * 1024 + 1)},
        )
        self.assertEqual(report_response.status_code, 422)

        body_response = await self.client.post(
            "/api/v1/investigations",
            headers={**self._mutation_headers("large-body"), "Content-Type": "application/json"},
            content=b" " * (32 * 1024 + 1),
        )
        self.assertEqual(body_response.status_code, 413)

    async def test_host_mismatch_is_rejected(self) -> None:
        response = await self.client.get("/api/v1/health", headers={"Host": "attacker.invalid"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_request")

    async def test_origin_fetch_metadata_and_csrf_are_each_enforced(self) -> None:
        invalid_headers = (
            {"Sec-Fetch-Site": "same-origin", "X-CSRF-Token": self.csrf_token},
            {"Origin": "null", "Sec-Fetch-Site": "same-origin", "X-CSRF-Token": self.csrf_token},
            {"Origin": "http://attacker.invalid", "Sec-Fetch-Site": "same-origin", "X-CSRF-Token": self.csrf_token},
            {"Origin": "http://127.0.0.1:3000", "Sec-Fetch-Site": "cross-site", "X-CSRF-Token": self.csrf_token},
            {"Origin": "http://127.0.0.1:3000", "Sec-Fetch-Site": "same-origin"},
            {"Origin": "http://127.0.0.1:3000", "Sec-Fetch-Site": "same-origin", "X-CSRF-Token": "wrong"},
        )
        for index, security_headers in enumerate(invalid_headers):
            with self.subTest(index=index):
                headers = {"Idempotency-Key": f"security-case-{index}", **security_headers}
                response = await self.client.post(
                    "/api/v1/investigations",
                    headers=headers,
                    json={"fixture_id": "discount-calculator", "report": "A report"},
                )
                self.assertEqual(response.status_code, 403)
                self.assertEqual(set(response.json()), {"code", "message", "request_id"})

    async def test_forwarded_headers_are_not_trusted_and_cors_is_not_enabled(self) -> None:
        response = await self.client.get(
            "/api/v1/health",
            headers={
                "Host": "127.0.0.1:8000",
                "X-Forwarded-Host": "attacker.invalid",
                "X-Forwarded-Proto": "https",
                "Origin": "http://attacker.invalid",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("access-control-allow-origin", response.headers)

    async def test_fixture_path_traversal_is_an_unknown_id_and_does_not_consume_key(self) -> None:
        headers = self._mutation_headers("traversal-key")
        response = await self.client.post(
            "/api/v1/investigations",
            headers=headers,
            json={"fixture_id": "../../outside", "report": "A report"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "unknown_fixture")

        retry = await self.client.post(
            "/api/v1/investigations",
            headers=headers,
            json={"fixture_id": "discount-calculator", "report": "A report"},
        )
        self.assertEqual(retry.status_code, 202)

    async def test_event_cursor_is_exclusive_and_csrf_is_not_cached(self) -> None:
        csrf = await self.client.get("/api/v1/csrf")
        self.assertEqual(csrf.headers["cache-control"], "no-store")
        created = await self.client.post(
            "/api/v1/investigations",
            headers=self._mutation_headers("cursor-key"),
            json={"fixture_id": "discount-calculator", "report": "A report"},
        )
        self.assertEqual(created.status_code, 202)
        events = await self.client.get(f"/api/v1/investigations/{created.json()['id']}/events?after=1")
        self.assertEqual(events.status_code, 200)
        self.assertTrue(all(item["sequence"] > 1 for item in events.json()["items"]))

    async def test_capacity_exhaustion_returns_503_without_consuming_idempotency_key(self) -> None:
        service = self.app.state.investigation_service
        reservations = [service.coordinator.reserve() for _ in range(self.app.state.settings.coordinator_capacity)]
        try:
            response = await self.client.post(
                "/api/v1/investigations",
                headers=self._mutation_headers("saturated-api-key"),
                json={"fixture_id": "discount-calculator", "report": "A report"},
            )
        finally:
            for reservation in reservations:
                reservation.release()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "coordinator_capacity_exhausted")
        self.assertEqual(set(response.json()), {"code", "message", "request_id"})
        self.assertIsNone(service.repository.get_idempotency("saturated-api-key"))