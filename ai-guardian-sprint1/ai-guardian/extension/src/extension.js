const vscode = require("vscode");

// Sprint 1: command-triggered stub, POSTs to the mock/local backend.
// Sprint 2: switch to on-save trigger + real /api/analyze + /api/explain calls.
// Sprint 4: replace console output with inline diagnostics (squiggles).
function activate(context) {
  const disposable = vscode.commands.registerCommand("aiGuardian.analyzeFile", async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showInformationMessage("Open a file to analyze.");
      return;
    }

    const code = editor.document.getText();
    const filePath = editor.document.fileName;

    try {
      const response = await fetch("http://localhost:4000/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ projectId: "local-dev", filePath, code })
      });
      const data = await response.json();
      vscode.window.showInformationMessage(
        `AI Guardian found ${data.findings?.length ?? 0} finding(s). See Debug Console.`
      );
      console.log(data);
    } catch (err) {
      vscode.window.showErrorMessage(`AI Guardian: could not reach backend (${err.message})`);
    }
  });

  context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = { activate, deactivate };
