from app.integrations.ai.protocols import InvestigationContext, ProposalProvider
from app.integrations.execution.protocols import ExecutionAdapter
from app.repositories.investigation_repository import InvestigationRepository
from app.services.fixture_service import FixtureService


class InvestigationWorker:
    def __init__(
        self,
        repository: InvestigationRepository,
        provider: ProposalProvider,
        execution: ExecutionAdapter,
        fixtures: FixtureService,
    ) -> None:
        self.repository = repository
        self.provider = provider
        self.execution = execution
        self.fixtures = fixtures

    def process(self, investigation_id: str) -> None:
        if not self.repository.start_analysis(investigation_id):
            return
        investigation = self.repository.get_detail(investigation_id)
        fixture_id = investigation["fixture_id"]
        fixture, source_ref, source_content = self.fixtures.read_source(fixture_id)
        if not self.repository.is_analyzing(investigation_id):
            return
        context = InvestigationContext(
            investigation_id=investigation_id,
            report=investigation["report"],
            fixture_id=fixture_id,
            fixture_title=fixture.title,
            fixture_language=fixture.language,
            fixture_revision=fixture.revision,
            source_path=source_ref["path"],
            source_content=source_content,
            source_line_start=source_ref["line_start"],
            source_line_end=source_ref["line_end"],
            source_revision=source_ref["revision"],
            source_content_hash=source_ref["content_hash"],
        )
        evidence = self.provider.generate(context)
        if not self.repository.is_analyzing(investigation_id):
            return
        evidence.append(self.execution.result(investigation_id, fixture_id))
        if not self.repository.is_analyzing(investigation_id):
            return
        self.repository.complete(investigation_id, evidence)