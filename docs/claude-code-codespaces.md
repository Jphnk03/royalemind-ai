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

Run a clone only for repositories not already present. If access fails, grant that Codespace access to the *specific* repository through GitHub's supported Codespaces permissions, or use the repository's own approved Codespace. Do not display or copy tokens. An existing Codespace may need authorization for additional private repositories; configuration in GitHub files does not grant that permission.

Choose the correct project folder before asking Claude to modify anything. Do not let one project's settings, environment variables or credentials bleed into another. Opening the same repository from another folder does not deploy it.

## Original ChatGPT Sites projects

Equipment Keeper and Crew Load are **native ChatGPT Sites**. A GitHub repo containing their verified source would only be a controlled development copy, not an automatic sync or deployment path. Before copying source, confirm actual Sites export/source access, secure backups, private permissions, and a reversible route to publish updates to the **existing** Sites. Do not create placeholder GitHub repositories or replace original sites.