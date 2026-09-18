# License Status And Publication Gate

This repository is a release candidate, not yet an open-source release. The
authors have not selected a project-level license. In the absence of a license,
copyright is reserved by default and public redistribution remains blocked.

Before changing the repository visibility or announcing a release:

1. Confirm ownership of each first-party source file and obtain any required
   coauthor or institutional approval.
2. Select a project license compatible with the intended use of optional
   BoxMOT and other third-party dependencies.
3. Add the approved `LICENSE` file.
4. Run `python scripts/check_public_release.py --strict-publication`.
5. Review dataset and checkpoint terms independently; they are not covered by
   the project license.

The package excludes raw datasets, checkpoints, third-party repositories,
credentials, machine-local caches, paper drafts, and prior development history.
