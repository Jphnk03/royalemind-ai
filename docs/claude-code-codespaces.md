# Claude Code on iPad and GitHub Codespaces

1. Open your existing GitHub Codespace for this repository or open a repository folder in an authorized existing Codespace. Do not create another Codespace unless you approve its potential compute/storage costs.
2. In the browser-based VS Code editor, go to Extensions and install **Claude Code** from **Anthropic** (`anthropic.claude-code`) if it is not already installed. This project recommends the same official extension.
3. Open the Claude Code sidebar or use the command palette **Claude Code: Open in New Tab**. Authenticate privately with **Anthropic Console** using the organization with your prepaid API credits. Never paste keys into chat or GitHub.
4. Read `CLAUDE.md` and `README.md`; first request: "Explain this repository and list safe tests. Do not edit, run migrations, call billable APIs, or deploy."
5. Before edits, check out a dedicated feature branch, use test-only dependencies/data, and open a draft PR.

## Reuse one Codespace safely

The VS Code extension runs inside the Codespace, not inside a particular GitHub repository. If its GitHub identity has access, you can clone another repository under `/workspaces`, then open that folder in the editor. Example, from a regular terminal:

```bash
gh auth status
gh repo clone Jphnk03/leadpilot-ai /workspaces/leadpilot-ai
gh repo clone Jphnk03/royalemind-ai /workspaces/royalemind-ai
```

Run a clone only for repositories not already present. If access fails, do not create a new Codespace or share credentials. GitHub documents using a repository-scoped **fine-grained personal access token**, kept privately in a Codespaces secret, for extra repositories in an **existing** Codespace. GitHub devcontainer repository permissions apply to **new Codespaces only**, not existing ones even after rebuild. Prefer minimal Contents permissions; ask the owner to authorize them privately. Do not print or paste tokens into chat. The existing Codespace may instead be kept to its original repository.

Choose the correct project folder before asking Claude to modify anything. Do not let one project's settings, environment variables or credentials bleed into another. Opening the same repository from another folder does not deploy it.

## Original ChatGPT Sites projects

Equipment Keeper and Crew Load are **native ChatGPT Sites**. A GitHub repo containing their verified source would only be a controlled development copy, not an automatic sync or deployment path. Before copying source, confirm actual Sites export/source access, secure backups, private permissions, and a reversible route to publish updates to the **existing** Sites. Do not create placeholder GitHub repositories or replace original sites.