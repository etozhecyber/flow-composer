# Flow Composer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A command-line tool to decompose and rebuild astrsk.ai Flow JSON configurations, enabling easier editing and management.

## Why Flow Composer?

The astrsk.ai platform includes a powerful visual editor for managing every aspect of a Flow. However, for those who prefer a **"Flow as Code"** workflow, managing complex configurations through a UI can present certain limitations.

This tool was created to empower a developer-centric workflow, addressing the following needs:

*   **Version Control:** To treat your Flow configuration like any other source code, allowing you to use Git to track changes, experiment in branches, and collaborate with a full history.
*   **Powerful Tooling:** To leverage your favorite code editor and its entire ecosystem, including AI assistants (like GitHub Copilot), advanced search and replace, linters, and custom scripts.
*   **Holistic View & Bulk Editing:** To see the entire structure of your project at a glance in a file tree, and to make sweeping changes across multiple prompts or schemas with ease, instead of navigating through separate UI windows.
*   **Reproducibility:** To be able to check out any version of your Flow from source control and rebuild the exact same JSON configuration.

`Flow Composer` is not a replacement for the astrsk.ai UI, but a companion tool designed to bring the power and flexibility of a local development environment to your Flow creation process.

## The Solution: Flow Composer

`Flow Composer` transforms this workflow. It's a CLI tool that acts as a bridge between the complex single-file JSON format and a human-friendly, structured directory of YAML and Markdown files.

The workflow is simple:

`flow.json` ➡️ **`unpack`** ➡️ `📂 Human-Readable Workspace` ➡️ **`edit`** ➡️ **`pack`** ➡️ `flow-updated.json`

This allows you to leverage the full power of your favorite code editor to craft and manage your agent's logic.

## Features

*   **Decompose** a single JSON file into a structured workspace of folders and files.
*   **Edit with Ease:** All prompts, schemas, and descriptions are converted to easy-to-edit YAML and Markdown files.
*   **Version Control Friendly:** The workspace structure is ideal for versioning with Git, allowing for clear diffs and collaborative editing.
*   **`!include` Directive:** Keep your YAML files clean by referencing long text content from separate `.md` files.
*   **Self-Contained Workspace:** The entire project state is stored within the workspace directory. No need to keep the original JSON for rebuilding.
*   **Rebuild with Confidence:** Pack the entire workspace back into a single, valid JSON file, ready for import.
*   **Preserves Structure:** All IDs, graph nodes, and edges are perfectly preserved during the `unpack` and `pack` process.

## Installation

1.  Clone the repository (or download the source code):
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
    cd YOUR_REPOSITORY
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Unpacking a Flow

To convert a `flow.json` file into a workspace directory:

```bash
# Syntax: python flow-composer.py unpack <source_json_path> <output_workspace_dir>
python flow-composer.py unpack ./my-flow.json ./my-flow-workspace
```

This will create the `my-flow-workspace` directory with the project structure.

### Packing a Flow

To build a final `json` file from your workspace directory:

```bash
# Syntax: python flow-composer.py pack <workspace_dir> <output_json_path>
python flow-composer.py pack ./my-flow-workspace ./my-flow-updated.json
```

This will generate `my-flow-updated.json`, which you can then import back into astrsk.ai

## Workspace File Structure

An unpacked project will look like this:

```
my-flow-workspace/
├── project_config.yaml      # Global project metadata
├── response_template.md     # The main response template
├── graph_nodes.yaml         # Graph node definitions
├── graph_edges.yaml         # Graph edge definitions
└── agents/
    └── AgentName/
        ├── agent_config.yaml
        ├── prompts/
        │   └── prompt_name.md
        └── schema/
            └── schema_field.md
```

## Building Executable

To create a standalone executable from the script:

1.  Install PyInstaller:
    ```bash
    pip install pyinstaller
    ```
2.  Run the build command:
    ```bash
    pyinstaller --onefile flow-composer.py
    ```
The executable will be created in the `dist/` directory.

## License

This project is licensed under the MIT License - see the LICENSE file for details.