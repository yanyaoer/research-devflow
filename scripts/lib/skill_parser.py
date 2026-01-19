"""Skill configuration parser - extracts config from SKILL.md files."""

import re
from pathlib import Path
from typing import Any

import yaml

from .types import SkillConfig


def parse_skill_config(content: str) -> dict[str, Any]:
    """Extract yaml:skill-config block from SKILL.md content.

    Args:
        content: The full content of a SKILL.md file.

    Returns:
        Parsed YAML configuration as a dictionary.
    """
    # Match ```yaml:skill-config ... ``` blocks
    pattern = r"```yaml:skill-config\n(.*?)```"
    match = re.search(pattern, content, re.DOTALL)

    if match:
        yaml_content = match.group(1)
        return yaml.safe_load(yaml_content) or {}

    return {}


def extract_prompts(content: str) -> dict[str, str]:
    """Extract named prompt blocks from SKILL.md content.

    Looks for blocks like:
    ```markdown:prompt-name
    prompt content here
    ```

    Args:
        content: The full content of a SKILL.md file.

    Returns:
        Dictionary mapping prompt names to their content.
    """
    prompts = {}
    # Match ```markdown:prompt-name ... ``` blocks
    pattern = r"```markdown:([a-zA-Z0-9_-]+)\n(.*?)```"
    matches = re.findall(pattern, content, re.DOTALL)

    for name, prompt_content in matches:
        prompts[name] = prompt_content.strip()

    return prompts


def extract_frontmatter(content: str) -> dict[str, Any]:
    """Extract YAML frontmatter from SKILL.md content.

    Args:
        content: The full content of a SKILL.md file.

    Returns:
        Parsed frontmatter as a dictionary.
    """
    # Match --- ... --- at the start of the file
    pattern = r"^---\n(.*?)\n---"
    match = re.match(pattern, content, re.DOTALL)

    if match:
        return yaml.safe_load(match.group(1)) or {}

    return {}


def load_skill(skill_path: str | Path) -> SkillConfig:
    """Load a skill configuration from a SKILL.md file.

    Args:
        skill_path: Path to the SKILL.md file or skill directory.

    Returns:
        SkillConfig object with all parsed configuration.

    Raises:
        FileNotFoundError: If the skill file doesn't exist.
        ValueError: If the skill configuration is invalid.
    """
    path = Path(skill_path)

    # If given a directory, look for SKILL.md inside
    if path.is_dir():
        path = path / "SKILL.md"

    if not path.exists():
        raise FileNotFoundError(f"Skill file not found: {path}")

    content = path.read_text(encoding="utf-8")

    # Try to get config from yaml:skill-config block first
    config_data = parse_skill_config(content)

    # Fall back to frontmatter for basic info if no skill-config block
    if not config_data:
        frontmatter = extract_frontmatter(content)
        if frontmatter:
            config_data = {
                "name": frontmatter.get("name", path.parent.name),
                "description": frontmatter.get("description", ""),
                "version": "1.0",
            }
        else:
            # Use directory name as skill name
            config_data = {
                "name": path.parent.name,
                "version": "1.0",
            }

    # Extract prompts from the document
    prompts = extract_prompts(content)
    config_data["prompts"] = prompts

    # Create SkillConfig object
    skill_config = SkillConfig.from_dict(config_data, source_file=str(path))

    return skill_config


def discover_skills(skills_dir: str | Path) -> list[SkillConfig]:
    """Discover all skills in a directory.

    Args:
        skills_dir: Path to the skills directory.

    Returns:
        List of SkillConfig objects for all discovered skills.
    """
    skills_path = Path(skills_dir)
    skills = []

    if not skills_path.exists():
        return skills

    for skill_dir in skills_path.iterdir():
        if skill_dir.is_dir():
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                try:
                    skill = load_skill(skill_file)
                    skills.append(skill)
                except (ValueError, yaml.YAMLError) as e:
                    # Log warning but continue discovering other skills
                    print(f"Warning: Failed to load skill from {skill_file}: {e}")

    return skills


def validate_skill_config(config: SkillConfig) -> list[str]:
    """Validate a skill configuration.

    Args:
        config: SkillConfig to validate.

    Returns:
        List of validation error messages. Empty if valid.
    """
    errors = []

    if not config.name:
        errors.append("Skill name is required")

    if not config.version:
        errors.append("Skill version is required")

    # Validate steps
    step_ids = set()
    for step in config.steps:
        if not step.id:
            errors.append(f"Step ID is required for step: {step.name}")
        if step.id in step_ids:
            errors.append(f"Duplicate step ID: {step.id}")
        step_ids.add(step.id)

        # Check prompt references
        if step.prompt_ref:
            ref = step.prompt_ref.lstrip("#")
            if ref not in config.prompts:
                errors.append(f"Step '{step.id}' references undefined prompt: {ref}")

        # Check dependencies
        for dep in step.dependencies:
            if dep not in step_ids and dep != step.id:
                # Dependency might be defined later, we'll check after all steps
                pass

    # Re-check dependencies after collecting all step IDs
    for step in config.steps:
        for dep in step.dependencies:
            if dep not in step_ids:
                errors.append(f"Step '{step.id}' has undefined dependency: {dep}")

    return errors
