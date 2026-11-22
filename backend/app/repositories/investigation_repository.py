import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Iterable

from app.core.errors import ConflictError, NotFoundError
from app.models.evidence import EvidenceRecord
from app.models.investigation import (
    EventType,
    ExecutionStatus,
    InvestigationStatus,
    InvalidStateTransition,
    VerificationOutcome,
    require_transition,
)
from app.repositories.database import Database


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class InvestigationRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get_idempotency(self, key: str) -> sqlite3.Row | None:
        connection = self.database.connect()
        try:
            return connection.execute(
                "SELECT request_hash, investigation_id FROM idempotency_records WHERE key = ?",
                (key,),
            ).fetchone()
        finally:
            connection.close()

    def create(
        self,
        investigation_id: str,
        fixture_id: str,
        report: str,
        idempotency_key: str,
        request_hash: str,
    ) -> dict[str, Any]:
        timestamp = utc_now()
        with self.database.transaction() as connection:
            connection.execute(
                """INSERT INTO investigations
                   (id, fixture_id, report, status, verification_outcome, execution_status,
                    created_at, updated_at, latest_event_sequence)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                (
                    investigation_id,
                    fixture_id,
                    report,
                    InvestigationStatus.QUEUED.value,
                    VerificationOutcome.NOT_RUN.value,
                    ExecutionStatus.NOT_REQUESTED.value,
                    timestamp,
                    timestamp,
                ),
            )
            connection.execute(
                "INSERT INTO idempotency_records (key, request_hash, investigation_id) VALUES (?, ?, ?)",
                (idempotency_key, request_hash, investigation_id),
            )
            connection.execute(
                """INSERT INTO investigation_events
                   (investigation_id, sequence, type, created_at, data_json)
                   VALUES (?, 1, ?, ?, ?)""",
                (
                    investigation_id,
                    EventType.QUEUED.value,
                    timestamp,
                    json.dumps({"status": InvestigationStatus.QUEUED.value}, separators=(",", ":")),
                ),
            )
        return {
            "id": investigation_id,
            "status": InvestigationStatus.QUEUED.value,
            "verification_outcome": VerificationOutcome.NOT_RUN.value,
            "execution_status": ExecutionStatus.NOT_REQUESTED.value,
        }

    def get_detail(self, investigation_id: str) -> dict[str, Any]:
        connection = self.database.connect()
        try:
            row = self._get_row(connection, investigation_id)
            evidence_rows = connection.execute(
                """SELECT id, kind, content_type, producer_kind, producer_version,
                          source_fixture_id, title, summary, source_ref_json
                   FROM evidence_items WHERE investigation_id = ? ORDER BY rowid""",
                (investigation_id,),
            ).fetchall()
            return {
                "id": row["id"],
                "fixture_id": row["fixture_id"],
                "report": row["report"],
                "status": row["status"],
                "verification_outcome": row["verification_outcome"],
                "execution_status": row["execution_status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "latest_event_sequence": row["latest_event_sequence"],
                "evidence": [self._evidence_payload(item) for item in evidence_rows],
            }
        finally:
            connection.close()

    def get_summary(self, investigation_id: str) -> dict[str, Any]:
        connection = self.database.connect()
        try:
            return self._summary(self._get_row(connection, investigation_id))
        finally:
            connection.close()

    def is_analyzing(self, investigation_id: str) -> bool:
        connection = self.database.connect()
        try:
            row = self._get_row(connection, investigation_id)
            return InvestigationStatus(row["status"]) is InvestigationStatus.ANALYZING
        finally:
            connection.close()

    def get_events(self, investigation_id: str, after: int, limit: int) -> dict[str, Any]:
        connection = self.database.connect()
        try:
            self._get_row(connection, investigation_id)
            rows = connection.execute(
                """SELECT sequence, type, created_at, data_json
                   FROM investigation_events
                   WHERE investigation_id = ? AND sequence > ?
                   ORDER BY sequence ASC LIMIT ?""",
                (investigation_id, after, limit + 1),
            ).fetchall()
            has_more = len(rows) > limit
            selected = rows[:limit]
            items = [
                {
                    "sequence": row["sequence"],
                    "type": row["type"],
                    "created_at": row["created_at"],
                    "data": json.loads(row["data_json"]),
                }
                for row in selected
            ]
            return {
                "items": items,
                "next_cursor": selected[-1]["sequence"] if has_more and selected else None,
            }
        finally:
            connection.close()

    def start_analysis(self, investigation_id: str) -> bool:
        return self.transition(
            investigation_id,
            InvestigationStatus.ANALYZING,
            EventType.ANALYSIS_STARTED,
            {"status": InvestigationStatus.ANALYZING.value},
        )

    def transition(
        self,
        investigation_id: str,
        requested: InvestigationStatus,
        event_type: EventType,
        data: dict[str, Any],
    ) -> bool:
        with self.database.transaction() as connection:
            row = self._get_row(connection, investigation_id)
            current = InvestigationStatus(row["status"])
            if requested is InvestigationStatus.ANALYZING and current in {
                InvestigationStatus.CANCELLED,
                InvestigationStatus.INTERRUPTED,
            }:
                return False
            try:
                require_transition(current, requested)
            except InvalidStateTransition as error:
                raise ConflictError() from error
            self._update_status(connection, row, requested, event_type, data)
            return True

    def complete(self, investigation_id: str, evidence: Iterable[EvidenceRecord]) -> bool:
        with self.database.transaction() as connection:
            row = self._get_row(connection, investigation_id)
            current = InvestigationStatus(row["status"])
            if current is InvestigationStatus.CANCELLED:
                return False
            try:
                require_transition(current, InvestigationStatus.REVIEWABLE)
            except InvalidStateTransition as error:
                raise ConflictError() from error
            evidence_ids = []
            timestamp = utc_now()
            for item in evidence:
                evidence_ids.append(item.id)
                connection.execute(
                    """INSERT INTO evidence_items
                       (id, investigation_id, kind, content_type, producer_kind, producer_version,
                        source_fixture_id, title, summary, source_ref_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item.id,
                        investigation_id,
                        item.kind.value,
                        item.content_type.value,
                        item.producer_kind.value,
                        item.producer_version,
                        item.source_fixture_id,
                        item.title,
                        item.summary,
                        json.dumps(item.source_ref, separators=(",", ":")) if item.source_ref else None,
                    ),
                )
                row = self._append_event(connection, row, EventType.EVIDENCE_ADDED, {"evidence_id": item.id}, timestamp)
            self._update_status(
                connection,
                row,
                InvestigationStatus.REVIEWABLE,
                EventType.REVIEWABLE,
                {"status": InvestigationStatus.REVIEWABLE.value, "evidence_ids": evidence_ids},
                timestamp=timestamp,
                execution_status=ExecutionStatus.SIMULATED,
            )
            return True

    def cancel(self, investigation_id: str) -> dict[str, Any]:
        with self.database.transaction() as connection:
            row = self._get_row(connection, investigation_id)
            current = InvestigationStatus(row["status"])
            if current is InvestigationStatus.CANCELLED:
                return self._summary(row)
            try:
                require_transition(current, InvestigationStatus.CANCELLED)
            except InvalidStateTransition as error:
                raise ConflictError() from error
            updated = self._update_status(
                connection,
                row,
                InvestigationStatus.CANCELLED,
                EventType.CANCELLED,
                {"status": InvestigationStatus.CANCELLED.value},
            )
            return self._summary(updated)

    def fail(self, investigation_id: str) -> None:
        with self.database.transaction() as connection:
            row = self._get_row(connection, investigation_id)
            if InvestigationStatus(row["status"]) is not InvestigationStatus.ANALYZING:
                return
            self._update_status(
                connection,
                row,
                InvestigationStatus.FAILED,
                EventType.FAILED,
                {"status": InvestigationStatus.FAILED.value, "message_code": "workflow_failed"},
            )

    def interrupt_enqueue_failure(self, investigation_id: str) -> None:
        with self.database.transaction() as connection:
            row = self._get_row(connection, investigation_id)
            if InvestigationStatus(row["status"]) is not InvestigationStatus.QUEUED:
                return
            self._update_status(
                connection,
                row,
                InvestigationStatus.INTERRUPTED,
                EventType.INTERRUPTED,
                {"status": InvestigationStatus.INTERRUPTED.value},
            )

    def recover_unfinished(self) -> int:
        recovered = 0
        with self.database.transaction() as connection:
            rows = connection.execute(
                "SELECT * FROM investigations WHERE status IN (?, ?) ORDER BY created_at",
                (InvestigationStatus.QUEUED.value, InvestigationStatus.ANALYZING.value),
            ).fetchall()
            for row in rows:
                self._update_status(
                    connection,
                    row,
                    InvestigationStatus.INTERRUPTED,
                    EventType.INTERRUPTED,
                    {"status": InvestigationStatus.INTERRUPTED.value},
                )
                recovered += 1
        return recovered

    def _get_row(self, connection: sqlite3.Connection, investigation_id: str) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM investigations WHERE id = ?", (investigation_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError()
        return row

    def _append_event(
        self,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
        event_type: EventType,
        data: dict[str, Any],
        timestamp: str,
    ) -> sqlite3.Row:
        sequence = row["latest_event_sequence"] + 1
        connection.execute(
            """INSERT INTO investigation_events
               (investigation_id, sequence, type, created_at, data_json)
               VALUES (?, ?, ?, ?, ?)""",
            (row["id"], sequence, event_type.value, timestamp, json.dumps(data, separators=(",", ":"))),
        )
        cursor = connection.execute(
            """UPDATE investigations
               SET latest_event_sequence = ?, updated_at = ?, version = version + 1
               WHERE id = ? AND version = ?""",
            (sequence, timestamp, row["id"], row["version"]),
        )
        if cursor.rowcount != 1:
            raise ConflictError()
        return self._get_row(connection, row["id"])

    def _update_status(
        self,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
        status: InvestigationStatus,
        event_type: EventType,
        data: dict[str, Any],
        timestamp: str | None = None,
        execution_status: ExecutionStatus | None = None,
    ) -> sqlite3.Row:
        timestamp = timestamp or utc_now()
        sequence = row["latest_event_sequence"] + 1
        values: list[Any] = [status.value, timestamp, sequence]
        sql = """UPDATE investigations
                 SET status = ?, updated_at = ?, latest_event_sequence = ?, version = version + 1"""
        if execution_status is not None:
            sql += ", execution_status = ?"
            values.append(execution_status.value)
        sql += " WHERE id = ? AND version = ?"
        values.extend([row["id"], row["version"]])
        cursor = connection.execute(sql, values)
        if cursor.rowcount != 1:
            raise ConflictError()
        connection.execute(
            """INSERT INTO investigation_events
               (investigation_id, sequence, type, created_at, data_json)
               VALUES (?, ?, ?, ?, ?)""",
            (row["id"], sequence, event_type.value, timestamp, json.dumps(data, separators=(",", ":"))),
        )
        return self._get_row(connection, row["id"])

    @staticmethod
    def _summary(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "status": row["status"],
            "verification_outcome": row["verification_outcome"],
            "execution_status": row["execution_status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "latest_event_sequence": row["latest_event_sequence"],
        }

    @staticmethod
    def _evidence_payload(row: sqlite3.Row) -> dict[str, Any]:
        evidence = {
            "id": row["id"],
            "kind": row["kind"],
            "content_type": row["content_type"],
            "producer_kind": row["producer_kind"],
            "producer_version": row["producer_version"],
            "title": row["title"],
            "summary": row["summary"],
        }
        if row["source_fixture_id"] is not None:
            evidence["source_fixture_id"] = row["source_fixture_id"]
        if row["source_ref_json"] is not None:
            evidence["source_ref"] = json.loads(row["source_ref_json"])
        return evidence