"""Exception types carrying process exit codes.

Exit-code convention, uniform across every subcommand:
    0  success
    1  the operation ran but failed
    2  environment or usage problem (missing dependency, missing key, bad args)

The scripts these replaced were inconsistent here — a missing dependency exited
1 in one script and 2 in two others, and one ``main()`` mixed ``sys.exit(2)``
with ``return 2``. ``cli/app.py`` now has the single handler.
"""


class TrueHandError(Exception):
    """Base for every error this tool raises deliberately."""

    exit_code = 1


class UserError(TrueHandError):
    """Bad input, bad environment, or a missing prerequisite the user controls."""

    exit_code = 2


class MissingDependency(UserError):
    """An optional extra is needed for this command but is not installed."""

    exit_code = 2


class OperationFailed(TrueHandError):
    """The work was attempted and did not succeed."""

    exit_code = 1
