# GitHub Release Checklist

The intended public repository name is **`REGR-Aerial-MOT`**. Keep the release
private until every publication gate below is complete.

## Before Renaming Or Publishing

- [ ] Review this independent release history; do not merge the development
  repository history, private data, paper drafts, or workstation artifacts.
- [ ] Obtain coauthor or institutional approval for the public code release.
- [ ] Select a project license and replace `LICENSE-STATUS.md` with the approved
  `LICENSE` while retaining applicable third-party notices.
- [ ] Run `python scripts/check_public_release.py --strict-publication`.
- [ ] Run the test, numerical verification, and summary-regeneration commands
  in `docs/REPRODUCIBILITY.md` on a clean checkout.
- [ ] Confirm that MMOT, M3OT, checkpoints, tracker caches, and derived images
  are linked by their official preparation instructions rather than uploaded.

## Repository Transition

1. Rename the private GitHub repository to `REGR-Aerial-MOT`.
2. Make this clean release history the default `main` branch only after review.
3. Copy `ci/github-actions.yml` to `.github/workflows/ci.yml` using GitHub
   credentials authorized to update workflows, then require it in branch
   protection.
4. Update the paper's code-availability URL after the final repository URL
   exists; do not claim that the code is public before visibility changes.
5. Create the first public tag only from the reviewed commit and archive its
   `SHA256SUMS` with the release notes.

GitHub normally redirects the old repository URL after a rename, but the paper,
project website, and citation metadata should still use the final canonical URL.
