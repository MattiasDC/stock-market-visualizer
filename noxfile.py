import os

import nox

FIX = os.getenv("FIX", "0") == "1"


def __black_cmd():
    black = ["black", "."]
    if not FIX:
        black.append("--check")
    return black


def __flake8_cmd():
    return ["flake8", "."]


def __isort_cmd():
    isort = ["isort", "."]
    if not FIX:
        isort.append("--check")
    return isort


def __yamllint_cmd():
    return ["yamllint", "."]


@nox.session(python="3.9")
def lint(session):
    session.install(".[dev]")
    session.run(*__black_cmd())
    session.run(*__flake8_cmd())
    session.run(*__isort_cmd())
    session.run(*__yamllint_cmd())
