"""Versioning, release and pull request automation for the GitHub Actions workflows.

Subcommands:
  tag              tag the tested commit on main with the next patch version
  release BUMP     tag main with the next minor or major version, publish a release
  ticket           make sure a pull request is linked to an issue
  automerge        squash-merge a pull request once all of its checks are green

Versions are git tags vMAJOR.MINOR.PATCH; nothing is written back to the repository.
Needs git and the GitHub CLI (gh, authenticated via GH_TOKEN), both preinstalled on
GitHub-hosted runners.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

SEMVER = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
CLOSING = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b:?\s+#(\d+)\b", re.IGNORECASE
)
EMPTY_CLOSING = re.compile(
    r"^[ \t]*(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?):?[ \t]+#[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)
BRANCH_TICKET = re.compile(r"(?:^|/)(?:issue-|gh-)?(\d+)(?:[-_]|$)")
PR_IN_SUBJECT = re.compile(r"\(#(\d+)\)$|^Merge pull request #(\d+) ")

CATEGORIES = [
    ("Breaking changes", {"breaking", "breaking change"}, ()),
    ("Dependencies", {"dependencies"}, ("bump ", "build(deps", "chore(deps", "deps")),
    ("Fixes", {"bug", "fix"}, ("fix",)),
    ("Features", {"enhancement", "feature"}, ("feat", "add ")),
    ("Documentation", {"documentation", "docs"}, ("docs",)),
]
OTHER = "Other changes"
ORDER = [
    "Breaking changes",
    "Features",
    "Fixes",
    "Documentation",
    "Dependencies",
    OTHER,
]
GREEN_CONCLUSIONS = {"SUCCESS", "NEUTRAL", "SKIPPED"}
LABELS = "labels(first: 20) { nodes { name } }"
PR_FIELDS = (
    f"number title author {{ login }} {LABELS}"
    f" closingIssuesReferences(first: 20) {{ nodes {{ number title {LABELS} }} }}"
)


# --- helpers ---------------------------------------------------------------


def run(*args: str, stdin: str | None = None) -> str:
    result = subprocess.run(
        args, input=stdin, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def gh_json(*args: str) -> object:
    return json.loads(run("gh", *args) or "null")


def repo() -> str:
    return os.environ["GITHUB_REPOSITORY"]


def event() -> dict:
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as fh:
        return json.load(fh)


def output(**values: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.writelines(f"{key}={value}\n" for key, value in values.items())


def summary(text: str) -> None:
    print(text)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")


# --- versions --------------------------------------------------------------


def parse(tag: str) -> tuple[int, int, int] | None:
    match = SEMVER.match(tag)
    return (int(match[1]), int(match[2]), int(match[3])) if match else None


def sort_versions(tags: list[str]) -> list[str]:
    return sorted((t for t in tags if parse(t)), key=parse)


def bump(latest: str | None, part: str) -> str:
    """Next version after `latest`.

    Without any tag, a minor release starts at 0.1.0 and a major one at 1.0.0.
    """
    if latest is None:
        return {"minor": "v0.1.0", "major": "v1.0.0", "patch": "v0.0.1"}[part]
    major, minor, patch = parse(latest)
    if part == "major":
        return f"v{major + 1}.0.0"
    if part == "minor":
        return f"v{major}.{minor + 1}.0"
    if part == "patch":
        return f"v{major}.{minor}.{patch + 1}"
    raise ValueError(f"unknown version part: {part}")


def previous_release(tags: list[str]) -> str | None:
    """Latest release tag (vX.Y.0) among `tags`, else the latest version tag."""
    versions = sort_versions(tags)
    releases = [t for t in versions if parse(t)[2] == 0]
    if releases:
        return releases[-1]
    return versions[-1] if versions else None


def version_tags(merged_into: str | None = None) -> list[str]:
    args = ["git", "tag", "--list", "v*"]
    if merged_into:
        args += ["--merged", merged_into]
    return sort_versions(run(*args).split())


def create_tag(tag: str, sha: str) -> None:
    run(
        "gh",
        "api",
        f"repos/{repo()}/git/refs",
        "-f",
        f"ref=refs/tags/{tag}",
        "-f",
        f"sha={sha}",
    )


def cmd_tag() -> int:
    sha = os.environ["GITHUB_SHA"]
    existing = sort_versions(run("git", "tag", "--points-at", sha).split())
    tags = version_tags()
    if existing:
        if existing[-1] != tags[-1]:
            # Re-run of an older commit: no version output, so nothing redeploys it.
            summary(f"{sha[:7]} is {existing[-1]}, older than {tags[-1]}; skipping.")
            return 0
        output(version=existing[-1])
        summary(f"{sha[:7]} is already tagged {existing[-1]}.")
        return 0
    if not tags:
        summary(
            "No version tag yet. Create the first release with the Release workflow."
        )
        return 0
    if tags[-1] not in version_tags(merged_into=sha):
        summary(f"{sha[:7]} is older than {tags[-1]}; not tagging it.")
        return 0
    new = bump(tags[-1], "patch")
    create_tag(new, sha)
    output(version=new)
    summary(f"Tagged {sha[:7]} as {new}.")
    return 0


# --- release notes ---------------------------------------------------------


def category(pr: dict) -> str:
    labels = {label.lower() for label in pr.get("labels", [])}
    for issue in pr.get("issues", []):
        labels |= {label.lower() for label in issue.get("labels", [])}
    title = pr["title"].lower()
    if pr.get("author") in ("dependabot", "dependabot[bot]", "app/dependabot"):
        return "Dependencies"
    for name, names, _ in CATEGORIES:
        if labels & names:
            return name
    for name, _, prefixes in CATEGORIES:
        if title.startswith(prefixes):
            return name
    return OTHER


def format_notes(
    repository: str,
    previous: str | None,
    new: str,
    prs: list[dict],
    commits: list[tuple[str, str]],
) -> str:
    """Release body: PRs by category, commits without a PR, closed tickets."""
    if previous is None:
        return (
            f"First release of {repository.split('/')[-1]} with semantic versioning.\n"
        )
    lines: list[str] = []
    groups: dict[str, list[dict]] = {}
    for pr in prs:
        groups.setdefault(category(pr), []).append(pr)
    for name in ORDER:
        if name in groups:
            lines += [f"## {name}", ""]
            lines += [
                f"- {pr['title']} (#{pr['number']})"
                for pr in sorted(groups[name], key=lambda p: p["number"])
            ]
            lines.append("")
    if commits:
        lines += ["## Commits without pull request", ""]
        lines += [f"- {subject} ({sha[:7]})" for sha, subject in commits]
        lines.append("")
    tickets = {
        issue["number"]: issue["title"] for pr in prs for issue in pr.get("issues", [])
    }
    if tickets:
        lines += ["## Closed tickets", ""]
        lines += [f"- #{number} {title}" for number, title in sorted(tickets.items())]
        lines.append("")
    if not prs and not commits:
        lines += [f"No changes since {previous}.", ""]
    lines.append(
        f"**Full changelog:** https://github.com/{repository}/compare/{previous}...{new}"
    )
    return "\n".join(lines) + "\n"


def commits_between(previous: str, sha: str) -> list[tuple[str, str]]:
    log = run(
        "git",
        "log",
        "--first-parent",
        "--reverse",
        "--format=%H%x1f%s",
        f"{previous}..{sha}",
    )
    return [tuple(line.split("\x1f", 1)) for line in log.splitlines() if line]


def pr_number_for(sha: str, subject: str) -> int | None:
    match = PR_IN_SUBJECT.search(subject)
    if match:
        return int(match[1] or match[2])
    pulls = gh_json("api", f"repos/{repo()}/commits/{sha}/pulls")
    merged = [p["number"] for p in pulls or [] if p.get("merged_at")]
    return merged[0] if merged else None


def fetch_prs(numbers: list[int]) -> list[dict]:
    owner, name = repo().split("/")
    prs: list[dict] = []
    for start in range(0, len(numbers), 40):
        fields = "\n".join(
            f"pr{n}: pullRequest(number: {n}) {{ {PR_FIELDS} }}"
            for n in numbers[start : start + 40]
        )
        query = (
            "query($owner: String!, $name: String!) {"
            f" repository(owner: $owner, name: $name) {{ {fields} }} }}"
        )
        data = gh_json(
            "api",
            "graphql",
            "-f",
            f"query={query}",
            "-F",
            f"owner={owner}",
            "-F",
            f"name={name}",
        )
        for node in data["data"]["repository"].values():
            if node:
                prs.append(
                    {
                        "number": node["number"],
                        "title": node["title"],
                        "author": (node.get("author") or {}).get("login", ""),
                        "labels": [label["name"] for label in node["labels"]["nodes"]],
                        "issues": [
                            {
                                "number": i["number"],
                                "title": i["title"],
                                "labels": [
                                    label["name"] for label in i["labels"]["nodes"]
                                ],
                            }
                            for i in node["closingIssuesReferences"]["nodes"]
                        ],
                    }
                )
    return prs


def build_notes(previous: str | None, sha: str, new: str) -> str:
    if previous is None:
        return format_notes(repo(), None, new, [], [])
    numbers: list[int] = []
    loose: list[tuple[str, str]] = []
    for commit, subject in commits_between(previous, sha):
        number = pr_number_for(commit, subject)
        if number is None:
            loose.append((commit, subject))
        elif number not in numbers:
            numbers.append(number)
    return format_notes(repo(), previous, new, fetch_prs(numbers), loose)


def cmd_release(part: str) -> int:
    if part not in ("minor", "major"):
        print(f"::error::Version part must be minor or major, not {part!r}.")
        return 1
    default = os.environ.get("DEFAULT_BRANCH", "main")
    if os.environ.get("GITHUB_REF") != f"refs/heads/{default}":
        print(f"::error::Releases are made from {default}.")
        return 1
    sha = os.environ["GITHUB_SHA"]
    tags = version_tags()
    new = bump(tags[-1] if tags else None, part)
    previous = previous_release(version_tags(merged_into=sha))
    notes = build_notes(previous, sha, new)
    run(
        "gh",
        "release",
        "create",
        new,
        "--target",
        sha,
        "--title",
        new,
        "--notes-file",
        "-",
        "--latest",
        stdin=notes,
    )
    output(version=new)
    # Optional (DISPATCH): redeploy so that an app showing its version shows it.
    dispatch(default)
    summary(
        f"Released {new} ({sha[:7]}), previous release {previous or 'none'}.\n\n{notes}"
    )
    return 0


# --- tickets ---------------------------------------------------------------


def closing_refs(body: str) -> list[int]:
    return [int(n) for n in CLOSING.findall(body or "")]


def ticket_from_branch(branch: str) -> int | None:
    match = BRANCH_TICKET.search(branch)
    return int(match[1]) if match else None


def with_ticket(body: str, number: int) -> str:
    """PR body that closes `number`.

    Fills an empty "Closes #" line from the PR template, or appends one.
    """
    body = body or ""
    if EMPTY_CLOSING.search(body):
        return EMPTY_CLOSING.sub(f"Closes #{number}", body, count=1)
    return (
        f"{body.rstrip()}\n\nCloses #{number}\n"
        if body.strip()
        else f"Closes #{number}\n"
    )


def is_issue(number: int) -> bool:
    try:
        data = gh_json("api", f"repos/{repo()}/issues/{number}")
    except RuntimeError:
        return False
    return isinstance(data, dict) and "pull_request" not in data


def linked_issue_count(number: int) -> int:
    owner, name = repo().split("/")
    query = (
        "query($owner: String!, $name: String!, $number: Int!) {"
        " repository(owner: $owner, name: $name) {"
        " pullRequest(number: $number) {"
        " closingIssuesReferences { totalCount } } } }"
    )
    data = gh_json(
        "api",
        "graphql",
        "-f",
        f"query={query}",
        "-F",
        f"owner={owner}",
        "-F",
        f"name={name}",
        "-F",
        f"number={number}",
    )
    return data["data"]["repository"]["pullRequest"]["closingIssuesReferences"][
        "totalCount"
    ]


def cmd_ticket() -> int:
    pr = event()["pull_request"]
    if pr["user"]["type"] == "Bot":
        # Dependabot and other bots need no ticket. Passing (not skipping) keeps
        # this run a successful trigger for Auto-merge.
        summary(f"Bot pull request by {pr['user']['login']}; no ticket needed.")
        return 0
    number, body, branch = pr["number"], pr.get("body") or "", pr["head"]["ref"]
    refs = [n for n in closing_refs(body) if is_issue(n)]
    if refs:
        summary(f"Closes {', '.join(f'#{n}' for n in refs)}.")
        return 0
    ticket = ticket_from_branch(branch)
    if ticket and is_issue(ticket):
        run(
            "gh",
            "api",
            "-X",
            "PATCH",
            f"repos/{repo()}/pulls/{number}",
            "-f",
            f"body={with_ticket(body, ticket)}",
        )
        summary(f"Linked #{ticket} from branch {branch}.")
        return 0
    if linked_issue_count(number):
        summary("Linked to an issue in the Development section.")
        return 0
    print(
        "::error::No ticket linked. Open an issue first, then either name the branch"
        " <issue>-<slug> (gh issue develop <issue> --checkout) or write"
        " 'Closes #<issue>' in the pull request description."
    )
    return 1


# --- auto-merge ------------------------------------------------------------


def rollup_state(checks: list[dict]) -> str:
    """'green' if every check succeeded, 'pending' while any runs, else 'failed'."""
    if not checks:
        return "pending"
    pending = False
    for check in checks:
        if check.get("__typename") == "StatusContext":
            state = check.get("state")
            if state in ("PENDING", "EXPECTED"):
                pending = True
            elif state != "SUCCESS":
                return "failed"
        elif check.get("status") != "COMPLETED":
            pending = True
        elif check.get("conclusion") not in GREEN_CONCLUSIONS:
            return "failed"
    return "pending" if pending else "green"


def merge_if_green(number: int, sha: str, default: str) -> bool:
    fields = "state,isDraft,headRefOid,baseRefName,isCrossRepository,statusCheckRollup"
    pr = gh_json("pr", "view", str(number), "--repo", repo(), "--json", fields)
    reason = None
    if pr["state"] != "OPEN":
        reason = f"is {pr['state'].lower()}"
    elif pr["isDraft"]:
        reason = "is a draft"
    elif pr["headRefOid"] != sha:
        reason = "has newer commits"
    elif pr["isCrossRepository"]:
        reason = "comes from a fork"
    elif pr["baseRefName"] != default:
        reason = f"targets {pr['baseRefName']}"
    else:
        state = rollup_state(pr["statusCheckRollup"])
        if state != "green":
            reason = (
                "has failing checks"
                if state == "failed"
                else "still has running checks"
            )
    if reason:
        print(f"PR #{number} {reason}; not merging.")
        return False
    try:
        run(
            "gh",
            "pr",
            "merge",
            str(number),
            "--repo",
            repo(),
            "--squash",
            "--match-head-commit",
            sha,
        )
    except RuntimeError:
        if (
            gh_json("pr", "view", str(number), "--repo", repo(), "--json", "state")[
                "state"
            ]
            == "MERGED"
        ):
            print(f"PR #{number} was merged by another run.")
            return False
        raise
    summary(f"Merged PR #{number}.")
    close_linked_issues(number)
    return True


def close_linked_issues(number: int) -> None:
    """Close the PR's tickets: GitHub skips that for merges made by the GITHUB_TOKEN."""
    owner, name = repo().split("/")
    query = (
        "query($owner: String!, $name: String!, $number: Int!) {"
        " repository(owner: $owner, name: $name) {"
        " pullRequest(number: $number) {"
        " closingIssuesReferences(first: 20) { nodes { number state } } } } }"
    )
    data = gh_json(
        "api",
        "graphql",
        "-f",
        f"query={query}",
        "-F",
        f"owner={owner}",
        "-F",
        f"name={name}",
        "-F",
        f"number={number}",
    )
    pr = data["data"]["repository"]["pullRequest"]
    for issue in pr["closingIssuesReferences"]["nodes"]:
        if issue["state"] == "OPEN":
            run(
                "gh",
                "issue",
                "close",
                str(issue["number"]),
                "--repo",
                repo(),
                "--reason",
                "completed",
                "--comment",
                f"Fixed by #{number}.",
            )
            print(f"Closed #{issue['number']}.")


def cmd_automerge() -> int:
    run_info = event()["workflow_run"]
    if run_info["event"] != "pull_request" or run_info["conclusion"] != "success":
        print("Not a successful pull request run; nothing to do.")
        return 0
    sha = run_info["head_sha"]
    default = os.environ.get("DEFAULT_BRANCH", "main")
    numbers = [p["number"] for p in run_info.get("pull_requests") or []]
    if not numbers:
        pulls = gh_json("api", f"repos/{repo()}/commits/{sha}/pulls") or []
        numbers = [
            p["number"]
            for p in pulls
            if p.get("state") == "open" and p["head"]["sha"] == sha
        ]
    merged = [n for n in numbers if merge_if_green(n, sha, default)]
    if merged:
        # Merges made with the GITHUB_TOKEN start no push workflows, so start them here.
        dispatch(default)
    return 0


def dispatch(branch: str) -> None:
    """Start the workflows listed in DISPATCH (space-separated files) on `branch`."""
    for workflow in os.environ.get("DISPATCH", "").split():
        run("gh", "workflow", "run", workflow, "--repo", repo(), "--ref", branch)
        print(f"Started {workflow} on {branch}.")


def main(argv: list[str]) -> int:
    commands = {"tag": cmd_tag, "ticket": cmd_ticket, "automerge": cmd_automerge}
    if len(argv) == 2 and argv[1] in commands:
        return commands[argv[1]]()
    if len(argv) == 3 and argv[1] == "release":
        return cmd_release(argv[2])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
