#!/usr/bin/env python3
"""Skill Runner CLI - Execute skills from command line.

Usage:
    uv run --isolated --with typer --with rich --with pyyaml scripts/skill-runner.py list
    uv run --isolated --with typer --with rich --with pyyaml scripts/skill-runner.py run research "task description"
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import typer

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.context import Context
from lib.executor import ExecutorRegistry
from lib.output import create_formatter
from lib.skill_parser import discover_skills, load_skill, validate_skill_config
from lib.types import SkillConfig, StepStatus, StepType

app = typer.Typer(
    name="skill-runner",
    help="Execute Research DevFlow skills from command line.",
    no_args_is_help=True,
)


def get_skills_dir() -> Path:
    """Get the skills directory."""
    script_dir = Path(__file__).parent.parent
    return script_dir / "skills"


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


@app.command()
def list_skills(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed info")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """List all available skills."""
    formatter = create_formatter(verbose=verbose, json_output=json_output)
    skills_dir = get_skills_dir()

    skills = discover_skills(skills_dir)

    if not skills:
        formatter.warning(f"No skills found in {skills_dir}")
        return

    if json_output:
        formatter.print_json([
            {
                "name": s.name,
                "version": s.version,
                "description": s.description,
                "steps": len(s.steps),
                "source": s.source_file,
            }
            for s in skills
        ])
    else:
        formatter.print_skill_list([
            {
                "name": s.name,
                "version": s.version,
                "description": s.description or "(no description)",
            }
            for s in skills
        ])

        if verbose:
            for skill in skills:
                formatter.info(f"\n{skill.name}:")
                formatter.info(f"  Source: {skill.source_file}")
                formatter.info(f"  Steps: {len(skill.steps)}")
                if skill.steps:
                    for step in skill.steps:
                        formatter.info(f"    - {step.id}: {step.name} ({step.type.value})")


@app.command()
def show(
    skill_name: Annotated[str, typer.Argument(help="Skill name to show")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Show details of a skill."""
    formatter = create_formatter(json_output=json_output)
    skills_dir = get_skills_dir()

    skill_path = skills_dir / skill_name
    if not skill_path.exists():
        formatter.error(f"Skill not found: {skill_name}")
        raise typer.Exit(1)

    try:
        skill = load_skill(skill_path)
    except Exception as e:
        formatter.error(f"Failed to load skill: {e}")
        raise typer.Exit(1)

    if json_output:
        formatter.print_json({
            "name": skill.name,
            "version": skill.version,
            "description": skill.description,
            "triggers": {
                "commands": skill.triggers.commands,
                "keywords": skill.triggers.keywords,
            },
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "type": s.type.value,
                }
                for s in skill.steps
            ],
            "prompts": list(skill.prompts.keys()),
            "source": skill.source_file,
        })
    else:
        formatter.print_panel(
            f"Version: {skill.version}\n"
            f"Description: {skill.description or '(none)'}\n"
            f"Steps: {len(skill.steps)}\n"
            f"Prompts: {len(skill.prompts)}",
            title=f"Skill: {skill.name}",
        )

        if skill.triggers.commands:
            formatter.info(f"Commands: {', '.join(skill.triggers.commands)}")
        if skill.triggers.keywords:
            formatter.info(f"Keywords: {', '.join(skill.triggers.keywords)}")

        if skill.steps:
            formatter.info("\nSteps:")
            for step in skill.steps:
                formatter.info(f"  [{step.id}] {step.name} ({step.type.value})")

        # Validate and show warnings
        errors = validate_skill_config(skill)
        if errors:
            formatter.warning("\nValidation warnings:")
            for err in errors:
                formatter.warning(f"  - {err}")


@app.command()
def run(
    skill_name: Annotated[str, typer.Argument(help="Skill name to run")],
    task: Annotated[str, typer.Argument(help="Task description")] = "",
    dry_run: Annotated[bool, typer.Option("--dry-run", "-n", help="Show what would be done")] = False,
    step_by_step: Annotated[bool, typer.Option("--step-by-step", help="Pause between steps")] = False,
    provider: Annotated[str, typer.Option("--provider", "-p", help="LLM provider")] = "",
    model: Annotated[str, typer.Option("--model", "-m", help="Model to use")] = "",
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    resume: Annotated[str, typer.Option("--resume", help="Resume from state file")] = "",
):
    """Run a skill with the given task."""
    formatter = create_formatter(verbose=verbose, json_output=json_output)
    skills_dir = get_skills_dir()

    # Load skill
    skill_path = skills_dir / skill_name
    if not skill_path.exists():
        formatter.error(f"Skill not found: {skill_name}")
        raise typer.Exit(1)

    try:
        skill = load_skill(skill_path)
    except Exception as e:
        formatter.error(f"Failed to load skill: {e}")
        raise typer.Exit(1)

    # Validate skill
    errors = validate_skill_config(skill)
    if errors:
        formatter.warning("Skill has validation issues:")
        for err in errors:
            formatter.warning(f"  - {err}")

    # Create or resume context
    if resume:
        try:
            context = Context.load(resume)
            formatter.info(f"Resumed from: {resume}")
        except FileNotFoundError:
            formatter.error(f"State file not found: {resume}")
            raise typer.Exit(1)
    else:
        # Generate task slug
        date_prefix = datetime.now().strftime("%y%m%d")
        task_slug = f"{date_prefix}-{skill_name}"
        if task:
            # Create a simple slug from task
            slug_part = task[:30].lower().replace(" ", "-")
            slug_part = "".join(c for c in slug_part if c.isalnum() or c == "-")
            task_slug = f"{date_prefix}-{slug_part}"

        context = Context(
            skill_name=skill.name,
            task_slug=task_slug,
        )
        context.set("task", task)
        context.set("task_slug", task_slug)
        context.set("project_root", str(get_project_root()))
        context.set("date", datetime.now().strftime("%Y-%m-%d"))

    # Show skill info
    formatter.info(f"Running skill: {skill.name} v{skill.version}")
    if task:
        formatter.info(f"Task: {task}")
    if dry_run:
        formatter.warning("DRY RUN - no changes will be made")

    # Initialize LLM provider (auto-detect if not specified)
    llm_provider = None
    tool_reg = None

    if not dry_run:
        try:
            from lib.llm_provider import get_provider, get_available_providers

            # Get available providers
            available = get_available_providers()

            # Use specified provider or auto-detect first available
            selected_provider = provider
            if not selected_provider and available:
                selected_provider = available[0]
                formatter.debug(f"Auto-detected provider: {selected_provider}")

            if selected_provider:
                if selected_provider not in available:
                    formatter.warning(f"Provider '{selected_provider}' not configured. Available: {available or 'none'}")
                    formatter.info("Configure in ~/.config/devflow/config.yml or set environment variables")
                else:
                    llm_provider = get_provider(selected_provider, model=model if model else None)
                    formatter.info(f"Using LLM provider: {selected_provider} (model: {llm_provider.default_model})")

                    # Create tool registry for tool calling
                    from lib.tool_registry import create_default_registry
                    tool_reg = create_default_registry(working_dir=str(get_project_root()))

        except ImportError as e:
            formatter.warning(f"LLM provider import failed: {e}")
        except Exception as e:
            formatter.warning(f"Failed to initialize LLM provider: {e}")

    # Create executor registry with provider
    registry = ExecutorRegistry(provider=llm_provider, tool_registry=tool_reg)

    # Execute steps
    total_duration = 0.0
    completed = 0
    failed = 0
    skipped = 0

    for step in skill.steps:
        # Skip already completed steps (when resuming)
        if context.is_step_completed(step.id):
            formatter.debug(f"Skipping completed step: {step.id}")
            skipped += 1
            continue

        context.current_step_id = step.id

        if step_by_step and not dry_run:
            input(f"\nPress Enter to execute step: {step.name}")

        # Check dependencies
        deps_satisfied = all(context.is_step_completed(dep) for dep in step.dependencies)
        if not deps_satisfied:
            formatter.warning(f"Skipping {step.id}: dependencies not met")
            skipped += 1
            continue

        # Execute step
        formatter.info(f"\n▶ Executing: {step.name}")
        result = registry.execute_step(step, context, skill, dry_run=dry_run)

        # Record result and store output in context for subsequent steps
        context.record_step_result(result)
        if result.output:
            # Store step output as variable (e.g., step "get_changes" -> ${get_changes_output})
            context.set(f"{step.id}_output", result.output)
            # Also store common variable names based on step id
            if step.id == "get_changes":
                context.set("changed_files", result.output)
            elif step.id == "load_rules":
                context.set("rules", result.output)
            elif step.id == "search_postmortem":
                context.set("postmortem_refs", result.output)
            elif step.id == "generate_report":
                # Auto-save report if LLM didn't use write_file tool
                report_dir = get_project_root() / ".claude" / "reviews" / context.task_slug
                report_file = report_dir / "REPORT.md"
                if not report_file.exists() and not dry_run:
                    report_dir.mkdir(parents=True, exist_ok=True)
                    report_file.write_text(result.output, encoding="utf-8")
                    formatter.info(f"  Report saved to: {report_file}")

        total_duration += result.duration

        # Print result
        formatter.print_step_result(
            step.name,
            result.status.value,
            output=result.output,
            error=result.error,
            duration=result.duration,
        )

        # Track counts
        if result.status == StepStatus.COMPLETED:
            completed += 1
        elif result.status == StepStatus.FAILED:
            failed += 1
            if step.type == StepType.GATE_CHECK:
                # Gate check failure - abort
                formatter.error("Gate check failed - aborting")
                break
        elif result.status == StepStatus.SKIPPED:
            skipped += 1

        # Save state after each step
        if not dry_run:
            state_dir = get_project_root() / ".claude" / "skill-runs"
            state_dir.mkdir(parents=True, exist_ok=True)
            state_file = state_dir / f"{context.task_slug}.json"
            context.save(state_file)

    # Print summary
    formatter.print_execution_summary(
        skill.name,
        len(skill.steps),
        completed,
        failed,
        skipped,
        total_duration,
    )

    if failed > 0:
        raise typer.Exit(1)


@app.command()
def status(
    state_file: Annotated[str, typer.Argument(help="State file to check")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Check status of a skill run."""
    formatter = create_formatter(json_output=json_output)

    try:
        context = Context.load(state_file)
    except FileNotFoundError:
        formatter.error(f"State file not found: {state_file}")
        raise typer.Exit(1)

    summary = context.get_state_summary()

    if json_output:
        formatter.print_json(summary)
    else:
        formatter.print_panel(
            f"Task: {summary['task_slug']}\n"
            f"Current Step: {summary['current_step']}\n"
            f"Completed: {summary['steps_completed']}/{summary['steps_total']}\n"
            f"Failed: {summary['steps_failed']}\n"
            f"Started: {summary['started_at']}\n"
            f"Updated: {summary['updated_at']}",
            title=f"Skill Run: {summary['skill_name']}",
        )


@app.command()
def validate(
    skill_name: Annotated[str, typer.Argument(help="Skill to validate")],
):
    """Validate a skill configuration."""
    formatter = create_formatter()
    skills_dir = get_skills_dir()

    skill_path = skills_dir / skill_name
    if not skill_path.exists():
        formatter.error(f"Skill not found: {skill_name}")
        raise typer.Exit(1)

    try:
        skill = load_skill(skill_path)
    except Exception as e:
        formatter.error(f"Failed to parse skill: {e}")
        raise typer.Exit(1)

    errors = validate_skill_config(skill)

    if errors:
        formatter.error(f"Skill '{skill_name}' has {len(errors)} validation error(s):")
        for err in errors:
            formatter.error(f"  - {err}")
        raise typer.Exit(1)
    else:
        formatter.success(f"Skill '{skill_name}' is valid")


@app.command()
def generate_instruction(
    skill_name: Annotated[str, typer.Argument(help="Skill name")],
    step_id: Annotated[str, typer.Argument(help="Step ID")],
    task: Annotated[str, typer.Option("--task", "-t", help="Task description")] = "",
):
    """Generate a JSON instruction for a step (for Claude Code integration)."""
    formatter = create_formatter(json_output=True)
    skills_dir = get_skills_dir()

    skill_path = skills_dir / skill_name
    if not skill_path.exists():
        formatter.error(f"Skill not found: {skill_name}")
        raise typer.Exit(1)

    try:
        skill = load_skill(skill_path)
    except Exception as e:
        formatter.error(f"Failed to load skill: {e}")
        raise typer.Exit(1)

    step = skill.get_step(step_id)
    if not step:
        formatter.error(f"Step not found: {step_id}")
        raise typer.Exit(1)

    # Create context
    context = Context(skill_name=skill.name)
    context.set("task", task)

    # Generate instruction
    registry = ExecutorRegistry()
    instruction = registry.generate_instruction(step, context, skill)

    print(json.dumps(instruction.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    app()
