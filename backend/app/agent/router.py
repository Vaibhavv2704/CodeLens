from app.services.report_service import ReportTool
from app.tools.github_tool import GitHubTool
from app.tools.llm_tool import LLMTool
from app.tools.repository_tool import RepositoryTool
from app.tools.source_inspection_tool import SourceInspectionTool
from app.tools.static_analysis_tool import StaticAnalysisTool
from app.tools.test_runner_tool import TestRunnerTool


def default_tools():
    return {t.name: t for t in [GitHubTool(), RepositoryTool(), StaticAnalysisTool(), TestRunnerTool(),
                              SourceInspectionTool(), LLMTool(), ReportTool()]}

