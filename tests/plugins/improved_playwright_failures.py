"""
Pytest plugin for enhanced Playwright testing.

Features:
- Automatically captures and logs console messages from Playwright pages during tests.
- On test failure, persists the rendered page HTML, a PNG screenshot, a concise text summary
  of the failure, and console logs in a per-test artifact directory (mirroring
  pytest-playwright's structure for screenshots/traces).
- Provides `assert_no_console_errors` helper to fail tests if any 'error' type console logs are detected.

The captured console logs are stored in `request.config._playwright_console_logs[nodeid]` as a list of dicts
for access in custom hooks/reporters if needed.

To disable:
- Change the `autouse=True` to `False` in the `playwright_console_logging` fixture.
- For failure artifacts, remove/comment out the `pytest_runtest_makereport` hook.
- The assertion is manual, so only impacts tests where it's called.

Configuration:
- Use the pytest ini option `playwright_console_ignore` to filter out console messages.
  These values are regular expressions and are matched against both the raw console text and the
  fully formatted line. Messages that match are not emitted to stdout and are not stored in the
  in-memory buffer used for artifacts.

  Example (pyproject.toml):
      [tool.pytest.ini_options]
      playwright_console_ignore = [
        "Invalid Sentry Dsn:.*",
        "Radar SDK: initialized.*",
        "\\[Meta Pixel\\].*",
      ]

  Example (pytest.ini):
      [pytest]
      playwright_console_ignore =
        Invalid Sentry Dsn:.*
        Radar SDK: initialized.*
        \\[Meta Pixel\\].*
"""

import logging
import re
from pathlib import Path
from typing import Generator, Protocol, TypedDict, cast

import pytest
from playwright.sync_api import ConsoleMessage, Page

from app import log

# Logger setup for Playwright JavaScript console output
logger = logging.getLogger("playwright_javascript")
logger.setLevel(logging.DEBUG)

# Regular expression to match and remove ANSI escape sequences (e.g., color codes) from text.
# This ensures clean, plain-text output for logs and failure summaries.
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


class StructuredConsoleLog(TypedDict):
    type: str
    text: str
    args: list[object]
    location: object


class FailureInfo(TypedDict):
    error_message: str | None
    error_file: str | None
    error_line: int | None
    longrepr_text: str | None


class PlaywrightConfig(Protocol):
    _playwright_console_logs: dict[str, list[StructuredConsoleLog]]
    _playwright_console_ignore_patterns: list[re.Pattern[str]]

    def getoption(self, name: str) -> object | None: ...
    def getini(self, name: str) -> object | None: ...


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register ini option for filtering Playwright console logs (no CLI flag)."""
    parser.addini(
        "playwright_console_ignore",
        "List of regex (one per line) to ignore Playwright console messages.",
        type="linelist",
        default=[],
    )


def _compile_ignore_patterns(config: PlaywrightConfig) -> list[re.Pattern[str]]:
    """Collect and compile ignore regex from ini configuration only."""
    ini_patterns = cast(list[str], config.getini("playwright_console_ignore") or [])

    unique_patterns: list[str] = []
    for pattern in ini_patterns:
        if pattern not in unique_patterns:
            unique_patterns.append(pattern)

    compiled: list[re.Pattern[str]] = [re.compile(p) for p in unique_patterns]
    return compiled


def pytest_configure(config: PlaywrightConfig) -> None:
    config._playwright_console_logs = {}
    # pre-compile regex filters for fast checks in the hot path
    config._playwright_console_ignore_patterns = _compile_ignore_patterns(config)


def format_console_msg(msg: StructuredConsoleLog) -> str:
    """Helper to format a console message dict into a log string."""
    args_str = ", ".join(str(arg) for arg in msg["args"]) if msg["args"] else "None"
    return f"Type: {msg['type']}, Text: {msg['text']}, Args: {args_str}, Location: {msg['location']}"


def extract_structured_log(msg: ConsoleMessage) -> StructuredConsoleLog:
    """Helper to extract console message into a structured dict."""
    return {
        "type": msg.type,
        "text": msg.text,
        "args": [arg.json_value() for arg in msg.args],
        "location": msg.location,
    }


def _should_ignore_console_log(
    structured_log: StructuredConsoleLog, patterns: list[re.Pattern[str]]
) -> bool:
    if not patterns:
        return False

    formatted = format_console_msg(structured_log)

    # check against both raw text and full formatted message for flexibility
    candidates = [structured_log["text"], formatted]

    for candidate in candidates:
        for pattern in patterns:
            if pattern.search(candidate):
                return True

    return False


@pytest.fixture(autouse=True)
def playwright_console_logging(
    request: pytest.FixtureRequest, pytestconfig: PlaywrightConfig
) -> Generator[None, None, None]:
    """Fixture to capture and log Playwright console messages."""
    if "page" not in request.fixturenames:
        yield
        return

    try:
        page: Page = request.getfixturevalue("page")
    except pytest.FixtureLookupError:
        yield
        return

    logs: list[StructuredConsoleLog] = []
    pytestconfig._playwright_console_logs[request.node.nodeid] = logs

    def log_console(msg: ConsoleMessage) -> None:
        structured_log = extract_structured_log(msg)
        # filter out ignored messages early so they don't hit stdout or memory
        if _should_ignore_console_log(
            structured_log, pytestconfig._playwright_console_ignore_patterns
        ):
            return
        logs.append(structured_log)
        log_msg = format_console_msg(structured_log)
        logger.debug(log_msg)

    page.on("console", log_console)
    yield


def assert_no_console_errors(request: pytest.FixtureRequest) -> None:
    """Assertion helper to ensure no 'error' type console logs occurred in the current test session.

    Call this at the end of your test or where you want to check up to that point.
    """
    config = cast(PlaywrightConfig, request.config)
    logs = config._playwright_console_logs.get(request.node.nodeid, [])
    errors = [log for log in logs if log["type"].lower() == "error"]
    error_msgs = "\n".join(format_console_msg(log) for log in errors)
    assert not errors, f"Console errors found:\n{error_msgs}"


def strip_ansi(text: str) -> str:
    """Helper to remove ANSI escape sequences from text."""
    try:
        return ANSI_ESCAPE_RE.sub("", text)
    except Exception:
        return text


def sanitize_for_artifacts(text: str) -> str:
    """Helper to sanitize test nodeid for artifact directory naming."""
    sanitized = re.sub(r"[^A-Za-z0-9]+", "-", text)
    sanitized = re.sub(r"-+", "-", sanitized).strip("-")
    return sanitized


def get_artifact_dir(item: pytest.Item) -> Path:
    """Helper to get or create the per-test artifact directory."""
    output_dir = item.config.getoption("output") or "test-results"
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    per_test_dir = output_path / sanitize_for_artifacts(item.nodeid)
    per_test_dir.mkdir(parents=True, exist_ok=True)
    return per_test_dir


def extract_failure_info(
    rep: pytest.TestReport, call: pytest.CallInfo[object], item: pytest.Item
) -> FailureInfo:
    """Helper to extract failure details from pytest report."""
    error_message = None
    error_file = None
    error_line = None
    longrepr_text = None

    # Extract error details from pytest's test report object
    if hasattr(rep, "longrepr") and rep.longrepr is not None:
        reprcrash = getattr(rep.longrepr, "reprcrash", None)
        if reprcrash is not None:
            error_message = getattr(reprcrash, "message", None)
            error_file = getattr(reprcrash, "path", None)
            error_line = getattr(reprcrash, "lineno", None)
        longrepr_text = getattr(rep, "longreprtext", None) or str(rep.longrepr)

    # Fallback: extract error message from call's exception info if not found in report
    if not error_message and hasattr(call, "excinfo") and call.excinfo is not None:
        try:
            error_message = call.excinfo.exconly()
        except Exception:
            error_message = (
                str(call.excinfo.value)
                if getattr(call.excinfo, "value", None)
                else None
            )

    # Fallback: use test item location if file/line not found in crash report
    if error_file is None or error_line is None:
        try:
            location_filename, location_lineno, _ = item.location
            error_file = error_file or location_filename
            error_line = error_line or location_lineno
        except Exception:
            error_file = error_file or str(item.nodeid)
            error_line = error_line or None

    return {
        "error_message": strip_ansi(error_message) if error_message else None,
        "error_file": error_file,
        "error_line": error_line,
        "longrepr_text": strip_ansi(longrepr_text) if longrepr_text else None,
    }


def write_failure_summary(
    per_test_dir: Path,
    item: pytest.Item,
    rep: pytest.TestReport,
    failure_info: FailureInfo,
) -> None:
    """Helper to write concise failure text summary."""
    from string import Template

    template_str = """test: $test_nodeid
phase: $phase
error: $error_message
location: $location

full failure:
$longrepr_text"""

    location = ""
    if failure_info["error_file"]:
        if failure_info["error_line"] is not None:
            location = f"{failure_info['error_file']}:{failure_info['error_line']}"
        else:
            location = failure_info["error_file"]

    template = Template(template_str)
    content = template.substitute(
        test_nodeid=item.nodeid,
        phase=rep.when,
        error_message=failure_info["error_message"] or "",
        location=location,
        longrepr_text=failure_info["longrepr_text"] or "",
    )

    content = strip_ansi(content)
    failure_text_file = per_test_dir / "failure.txt"
    failure_text_file.write_text(content)
    log.info("Wrote test failure summary", file_path=failure_text_file)


def write_console_logs(
    per_test_dir: Path, config: PlaywrightConfig, nodeid: str
) -> None:
    """Helper to write captured console logs to a file."""
    if nodeid in config._playwright_console_logs:
        logs = config._playwright_console_logs[nodeid]
        logs_content = "\n".join(format_console_msg(log) for log in logs)
        logs_file = per_test_dir / "console_logs.log"
        logs_file.write_text(logs_content)
        log.info("Wrote console logs", file_path=logs_file)
        del config._playwright_console_logs[nodeid]


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[object]
) -> Generator[None, object, None]:
    """Hook to persist page HTML, screenshot, failure summary, and console logs on test failure."""
    outcome = yield

    class _HookOutcome(Protocol):
        def get_result(self) -> pytest.TestReport: ...

    rep = cast(_HookOutcome, outcome).get_result()

    fixturenames = cast(list[str], getattr(item, "fixturenames", []))
    if rep.when == "call" and rep.failed and "page" in fixturenames:
        try:
            funcargs = cast(dict[str, object], getattr(item, "funcargs", {}))
            page = cast(Page, funcargs["page"])  # type: ignore[index]
            per_test_dir = get_artifact_dir(item)

            failure_file = per_test_dir / "failure.html"
            failure_file.write_text(page.content())
            log.info("Wrote rendered playwright page HTML", file_path=failure_file)

            screenshot_file = per_test_dir / "screenshot.png"
            page.screenshot(path=str(screenshot_file), full_page=True)
            log.info("wrote playwright screenshot", file_path=screenshot_file)

            failure_info = extract_failure_info(rep, call, item)
            write_failure_summary(per_test_dir, item, rep, failure_info)

            write_console_logs(
                per_test_dir, cast(PlaywrightConfig, item.config), item.nodeid
            )
        except Exception:
            log.exception("Error writing playwright failure artifacts")
