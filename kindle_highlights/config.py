import yaml
from pathlib import Path
from typing import Tuple

def get_config(yaml_path: str) -> Tuple[str, str]:
    """Load configuration from a YAML file.

    Args:
        yaml_path: Path to the YAML configuration file.

    Returns:
        A tuple containing the Notion API token and database ID.
    """
    with open(Path(yaml_path), "r") as config_file:
        config = yaml.safe_load(config_file)
        return config["token"], config["database_id"]
