from norway_job_market_intelligence import __version__
from norway_job_market_intelligence.config import PROJECT_NAME


def test_package_version() -> None:
    assert __version__ == "0.1.0"


def test_project_name() -> None:
    assert PROJECT_NAME == "Norway Job Market Intelligence Platform"
