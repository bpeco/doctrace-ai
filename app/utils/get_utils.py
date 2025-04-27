from git import Repo
from typing import List, Tuple

def get_repo_diff(repo_path: str, old_rev: str, new_rev: str) -> Tuple[List[str], str]:
    """
    Returns a tuple containing:
      1. A list of changed file paths between two revisions.
      2. The full unified diff text.

    :param repo_path: Path to the local git repository.
    :param old_rev: The old commit SHA ("before").
    :param new_rev: The new commit SHA ("after").
    :return: (changed_files, diff_text)
    """
    repo = Repo(repo_path)
    old = repo.commit(old_rev)
    new = repo.commit(new_rev)

    # Get diff index between revisions
    diffs = old.diff(new, create_patch=True)

    changed_files = []
    diff_lines = []
    for diff in diffs:
        # record file path
        path = diff.a_path or diff.b_path
        changed_files.append(path)
        # collect patch text
        diff_lines.append(diff.diff.decode('utf-8', errors='ignore'))

    diff_text = '\n'.join(diff_lines)
    return changed_files, diff_text
