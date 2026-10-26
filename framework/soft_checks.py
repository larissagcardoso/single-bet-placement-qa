"""Soft assertions: every check is reported, and the test fails once at the end with all mismatches."""
import allure


class SoftChecks:
    def __init__(self) -> None:
        self.failures: list[str] = []

    def check(self, label: str, actual, expected) -> None:
        # Each check is its own report step, shown green or red; a mismatch does not stop the test.
        try:
            with allure.step(f"Check {label}: expected {expected}"):
                assert actual == expected, f"got {actual}"
        except AssertionError:
            self.failures.append(f"{label}: expected {expected!r}, got {actual!r}")

    def assert_all(self, summary: str) -> None:
        assert not self.failures, f"{summary}:\n- " + "\n- ".join(self.failures)
