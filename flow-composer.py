import sys
import json
import yaml
import collections
from pathlib import Path
from typing import Any, Dict, Optional

# This order is used to maintain a consistent structure in the output JSON
DEFAULT_KEY_ORDER = [
    'name', 'description', 'nodes', 'edges', 'agents', 'responseTemplate',
    'createdAt', 'updatedAt', 'panelStructure', 'viewport'
]

class Include(str):
    """Marker for !include directive"""
    pass

class YamlIncludeDumper(yaml.SafeDumper):
    """Custom dumper to handle !include tags"""
    pass

def include_representer(dumper, data):
    """Representer for the Include class"""
    return dumper.represent_scalar('!include', str(data))

YamlIncludeDumper.add_representer(Include, include_representer)

def ordered_dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

YamlIncludeDumper.add_representer(collections.OrderedDict, ordered_dict_representer)


def make_include_loader(base_path: Path):
    """Factory function to create a custom YAML loader with !include support"""
    class YamlIncludeLoader(yaml.SafeLoader):
        def __init__(self, stream):
            self.base_path = base_path
            super().__init__(stream)

        def include(self, node):
            # Get file path from YAML node
            file_path = Path(self.construct_scalar(node))

            # Handle relative paths
            if not file_path.is_absolute():
                file_path = self.base_path / file_path

            # Read and return file content without newline translation
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                return f.read()

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return collections.OrderedDict(loader.construct_pairs(node))

    # Register the !include tag handler
    YamlIncludeLoader.add_constructor('!include', YamlIncludeLoader.include)
    YamlIncludeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    return YamlIncludeLoader

def load_yaml_with_includes(file_path: Path) -> Dict[str, Any]:
    """Load YAML file with support for !include directives"""
    with open(file_path, 'r', encoding='utf-8') as f:
        loader_class = make_include_loader(file_path.parent)
        return yaml.load(f, Loader=loader_class)

def save_yaml(data: Any, file_path: Path):
    """Save data to YAML file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=YamlIncludeDumper, allow_unicode=True, sort_keys=False, width=120)

def unpack(source_json: Path, output_dir: Optional[Path] = None):
    """Unpack JSON into workspace structure"""
    if output_dir is None:
        output_dir = source_json.with_suffix('')
    print(f"Unpacking {source_json} to {output_dir}")

    # Create output directory structure
    output_dir.mkdir(parents=True, exist_ok=True)
    agents_dir = output_dir / "agents"
    agents_dir.mkdir(exist_ok=True)

    # Load source JSON
    with open(source_json, 'r', encoding='utf-8') as f:
        source_data = json.load(f, object_pairs_hook=collections.OrderedDict)

    # Create root config files
    root_config = collections.OrderedDict(
        (k, v) for k, v in source_data.items()
        if k not in ['nodes', 'edges', 'agents', 'responseTemplate']
    )

    # Save project_config.yaml
    project_config_path = output_dir / "project_config.yaml"
    save_yaml(root_config, project_config_path)

    # Save response_template.md
    if 'responseTemplate' in source_data:
        response_template = source_data['responseTemplate']
        response_template_path = output_dir / "response_template.md"
        response_template_path.write_text(response_template, encoding='utf-8', newline='')
        # Update project_config to use !include
        root_config['responseTemplate'] = Include('response_template.md')
        save_yaml(root_config, project_config_path)

    # Save graph files
    if 'nodes' in source_data:
        graph_nodes_path = output_dir / "graph_nodes.yaml"
        save_yaml(source_data['nodes'], graph_nodes_path)

    if 'edges' in source_data:
        graph_edges_path = output_dir / "graph_edges.yaml"
        save_yaml(source_data['edges'], graph_edges_path)

    # Process agents
    if 'agents' in source_data:
        for agent_id, agent_data in source_data['agents'].items():
            agent_name = agent_data.get('name', agent_id)
            agent_dir = agents_dir / agent_name
            agent_dir.mkdir(exist_ok=True)

            # Create directories for prompts and schema
            prompts_dir = agent_dir / "prompts"
            prompts_dir.mkdir(exist_ok=True)
            schema_dir = agent_dir / "schema"
            schema_dir.mkdir(exist_ok=True)

            # Process prompt messages
            if 'promptMessages' in agent_data:
                for msg in agent_data['promptMessages']:
                    if 'promptBlocks' in msg:
                        for block in msg['promptBlocks']:
                            if 'template' in block and block['template']:
                                # Generate safe filename
                                safe_name = "".join(c if c.isalnum() else "_" for c in block.get('name', 'template'))
                                file_path = prompts_dir / f"{safe_name}.md"
                                file_path.write_text(block['template'], encoding='utf-8', newline='')
                                # Replace template with include directive
                                block['template'] = Include(f"prompts/{safe_name}.md")

            # Process schema fields
            if 'schemaFields' in agent_data:
                for field in agent_data['schemaFields']:
                    if 'description' in field and field['description']:
                        # Generate safe filename
                        safe_name = "".join(c if c.isalnum() else "_" for c in field.get('name', 'field'))
                        file_path = schema_dir / f"{safe_name}.md"
                        file_path.write_text(field['description'], encoding='utf-8', newline='')
                        # Replace description with include directive
                        field['description'] = Include(f"schema/{safe_name}.md")

            # Add agentId to the data so we can retrieve it during pack
            agent_data['agentId'] = agent_id

            # Create agent config with replaced values
            agent_config_path = agent_dir / "agent_config.yaml"
            save_yaml(agent_data, agent_config_path)

def pack(workspace_dir: Path, output_json: Optional[Path] = None):
    """Pack workspace into JSON"""
    if output_json is None:
        output_json = workspace_dir.with_suffix('.json')
    print(f"Packing {workspace_dir} to {output_json}")

    # --- 1. Load all data into temporary variables ---

    project_config_data = collections.OrderedDict()
    project_config_path = workspace_dir / "project_config.yaml"
    if project_config_path.exists():
        project_config_data = load_yaml_with_includes(project_config_path)

    nodes_data = None
    graph_nodes_path = workspace_dir / "graph_nodes.yaml"
    agent_id_order = []
    if graph_nodes_path.exists():
        nodes_data = load_yaml_with_includes(graph_nodes_path)
        if isinstance(nodes_data, list):
            for node in nodes_data:
                if isinstance(node, dict) and node.get('type') == 'agent':
                    data = node.get('data')
                    if isinstance(data, dict) and data.get('agentId'):
                        agent_id_order.append(data['agentId'])

    edges_data = None
    graph_edges_path = workspace_dir / "graph_edges.yaml"
    if graph_edges_path.exists():
        edges_data = load_yaml_with_includes(graph_edges_path)

    agents_data = None
    agents_dir = workspace_dir / "agents"
    if agents_dir.exists():
        all_agents = {}
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir():
                agent_config_path = agent_dir / "agent_config.yaml"
                if agent_config_path.exists():
                    agent_data = load_yaml_with_includes(agent_config_path)
                    agent_id = agent_data.get('agentId', agent_data.get('id'))
                    if agent_id:
                        if 'agentId' in agent_data: del agent_data['agentId']
                        if 'id' in agent_data: del agent_data['id']
                        all_agents[agent_id] = agent_data

        ordered_agents = collections.OrderedDict()
        for agent_id in agent_id_order:
            if agent_id in all_agents:
                ordered_agents[agent_id] = all_agents[agent_id]

        if ordered_agents:
            agents_data = ordered_agents

    # --- 2. Combine into a single dictionary ---

    full_data = collections.OrderedDict()
    full_data.update(project_config_data)
    if nodes_data is not None:
        full_data['nodes'] = nodes_data
    if edges_data is not None:
        full_data['edges'] = edges_data
    if agents_data is not None:
        full_data['agents'] = agents_data

    # --- 3. Order the dictionary ---

    result = collections.OrderedDict()
    # Add keys based on the default order
    for key in DEFAULT_KEY_ORDER:
        if key in full_data:
            result[key] = full_data[key]

    # Add any remaining keys that were not in the default order
    for key, value in full_data.items():
        if key not in result:
            result[key] = value

    # --- 4. Save final JSON ---
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, sort_keys=False)

if __name__ == "__main__":
    import argparse
    import traceback

    parser = argparse.ArgumentParser(description='Transform FLOW configurations between JSON and workspace format')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Unpack command
    unpack_parser = subparsers.add_parser('unpack', help='Convert JSON to workspace format')
    unpack_parser.add_argument('source_json', type=Path, help='Source JSON file path')
    unpack_parser.add_argument('output_dir', type=Path, nargs='?', help='Output directory for workspace. Defaults to the name of the source JSON file.')

    # Pack command
    pack_parser = subparsers.add_parser('pack', help='Convert workspace to JSON format')
    pack_parser.add_argument('workspace_dir', type=Path, help='Workspace directory')
    pack_parser.add_argument('output_json', type=Path, nargs='?', help='Output JSON file path. Defaults to the name of the workspace directory with a .json extension.')

    args = parser.parse_args()

    try:
        if args.command == 'unpack':
            unpack(args.source_json, args.output_dir)
        elif args.command == 'pack':
            pack(args.workspace_dir, args.output_json)
        print("Operation completed successfully.")
    except FileNotFoundError as e:
        print(f"Error: File not found - {e.filename}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"YAML parsing error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)