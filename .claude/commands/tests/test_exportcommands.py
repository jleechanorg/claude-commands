# ruff: noqa: S603, S607, PLR0915
import os
import subprocess
import shutil
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXPORT_SCRIPT = PROJECT_ROOT / ".claude" / "commands" / "exportcommands.sh"

@pytest.mark.skipif(shutil.which("rsync") is None, reason="rsync is required for exportcommands script")
def test_exportcommands_hermes_sync(tmp_path: Path):

    home_dir = tmp_path / "home"
    global_claude = home_dir / ".claude"
    hermes_home = home_dir / ".hermes"
    project_dir = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    fake_origin = tmp_path / "fake_origin"
    export_output = tmp_path / "export_output"
    debug_log = tmp_path / "mock_claude.log"

    global_claude.mkdir(parents=True)
    hermes_home.mkdir(parents=True)
    project_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    fake_origin.mkdir(parents=True)
    export_output.mkdir(parents=True)

    # Fake origin repo
    subprocess.run(["git", "init", "-b", "main", str(fake_origin)], check=True)
    subprocess.run(["git", "config", "user.email", "test@test-fixture.invalid"], cwd=fake_origin, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=fake_origin, check=True)

    # Write a mock README with >20 lines to satisfy the validity check
    readme = fake_origin / "README.md"
    readme.write_text("# Claude Commands\n" + "\n".join(f"Line {i}" for i in range(30)) + "\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=fake_origin, check=True)
    subprocess.run(["git", "commit", "-m", "initial commit"], cwd=fake_origin, check=True)

    # Mock 'gh'
    mock_gh = bin_dir / "gh"
    mock_gh.write_text(f"""#!/usr/bin/env bash
if [[ "$1" == "repo" && "$2" == "clone" ]]; then
    git clone "{fake_origin}" "$4"
    exit 0
elif [[ "$1" == "pr" && "$2" == "create" ]]; then
    echo "Mock PR created successfully"
    exit 0
else
    exit 0
fi
""", encoding="utf-8")
    mock_gh.chmod(0o755)

    # Mock 'claude' - copies files from the cloned repository in tmp to export_output
    mock_claude = bin_dir / "claude"
    mock_claude.write_text(f"""#!/usr/bin/env bash
echo "mock_claude invoked" >> "{debug_log}"
echo "PWD: $(pwd)" >> "{debug_log}"
# Search system tmp/var/folders for a claude-commands dir containing our global_cmd.md
REPO_DIR_PATH=""
for dir in $(find /var/folders /tmp -name "claude-commands" -type d 2>/dev/null); do
    if [[ -f "$dir/.claude/commands/global_cmd.md" ]]; then
        REPO_DIR_PATH="$dir"
        break
    fi
done

echo "REPO_DIR_PATH: $REPO_DIR_PATH" >> "{debug_log}"
if [[ -n "$REPO_DIR_PATH" ]]; then
    cp -r "$REPO_DIR_PATH"/. "{export_output}"
    echo "copied successfully" >> "{debug_log}"
else
    echo "REPO_DIR_PATH empty" >> "{debug_log}"
fi
echo "Mock readme content"
exit 0
""", encoding="utf-8")
    mock_claude.chmod(0o755)

    # Populate dummy files
    (global_claude / "commands").mkdir()
    (global_claude / "commands" / "global_cmd.md").write_text("# Global Cmd\n", encoding="utf-8")
    (global_claude / "skills").mkdir()
    (global_claude / "skills" / "global_skill").mkdir()
    (global_claude / "skills" / "global_skill" / "SKILL.md").write_text("# Global Skill\n", encoding="utf-8")

    (project_dir / ".claude" / "commands").mkdir(parents=True)
    (project_dir / ".claude" / "commands" / "project_cmd.md").write_text("# Project Cmd\n", encoding="utf-8")
    (project_dir / "orchestration").mkdir()
    (project_dir / "orchestration" / "runner.py").write_text("# runner code\n/Users/jleechan/some_path\n", encoding="utf-8")

    (hermes_home / "commands").mkdir()
    (hermes_home / "commands" / "hermes_cmd.sh").write_text("#!/usr/bin/env bash\necho hermes\n", encoding="utf-8")
    (hermes_home / "skills").mkdir()
    (hermes_home / "skills" / "hermes_skill").mkdir()
    (hermes_home / "skills" / "hermes_skill" / "SKILL.md").write_text("# Hermes Skill\n", encoding="utf-8")

    # Run the script
    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    env["PROJECT_ROOT"] = str(project_dir)
    env["HERMES_HOME"] = str(hermes_home)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(
        ["/bin/bash", "-x", str(EXPORT_SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    if debug_log.is_file():
        print("DEBUG LOG:", debug_log.read_text(encoding="utf-8"))

    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify synced files in the exported output
    assert (export_output / ".claude" / "commands" / "global_cmd.md").is_file()
    assert (export_output / ".claude" / "commands" / "project_cmd.md").is_file()
    assert (export_output / "orchestration" / "runner.py").is_file()

    # Check that content filters were applied (stripping /Users/jleechan to $HOME)
    filtered_code = (export_output / "orchestration" / "runner.py").read_text(encoding="utf-8")
    assert "$HOME/some_path" in filtered_code
    assert "/Users/jleechan" not in filtered_code

    # Verify hermes files are synced
    assert (export_output / "hermes" / "commands" / "hermes_cmd.sh").is_file()
    assert (export_output / "hermes" / "skills" / "hermes_skill" / "SKILL.md").is_file()


@pytest.mark.skipif(shutil.which("rsync") is None, reason="rsync is required for exportcommands script")
def test_exportcommands_hermes_soft_skip(tmp_path: Path):
    # Test soft skip behavior when hermes dir does not exist
    home_dir = tmp_path / "home"
    global_claude = home_dir / ".claude"
    project_dir = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    fake_origin = tmp_path / "fake_origin"
    export_output = tmp_path / "export_output"
    debug_log = tmp_path / "mock_claude_soft.log"

    global_claude.mkdir(parents=True)
    project_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    fake_origin.mkdir(parents=True)
    export_output.mkdir(parents=True)

    # Fake origin repo
    subprocess.run(["git", "init", "-b", "main", str(fake_origin)], check=True)
    subprocess.run(["git", "config", "user.email", "test@test-fixture.invalid"], cwd=fake_origin, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=fake_origin, check=True)

    readme = fake_origin / "README.md"
    readme.write_text("# Claude Commands\n" + "\n".join(f"Line {i}" for i in range(30)) + "\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=fake_origin, check=True)
    subprocess.run(["git", "commit", "-m", "initial commit"], cwd=fake_origin, check=True)

    # Mock 'gh' and 'claude'
    mock_gh = bin_dir / "gh"
    mock_gh.write_text(f"""#!/usr/bin/env bash
if [[ "$1" == "repo" && "$2" == "clone" ]]; then
    git clone "{fake_origin}" "$4"
    exit 0
else
    exit 0
fi
""", encoding="utf-8")
    mock_gh.chmod(0o755)

    mock_claude = bin_dir / "claude"
    mock_claude.write_text(f"""#!/usr/bin/env bash
echo "mock_claude invoked" >> "{debug_log}"
REPO_DIR_PATH=""
for dir in $(find /var/folders /tmp -name "claude-commands" -type d 2>/dev/null); do
    if [[ -f "$dir/.claude/commands/global_cmd.md" ]]; then
        REPO_DIR_PATH="$dir"
        break
    fi
done
echo "REPO_DIR_PATH: $REPO_DIR_PATH" >> "{debug_log}"
if [[ -n "$REPO_DIR_PATH" ]]; then
    cp -r "$REPO_DIR_PATH"/. "{export_output}"
fi
exit 0
""", encoding="utf-8")
    mock_claude.chmod(0o755)

    (global_claude / "commands").mkdir()
    # Write a dummy file so git commit doesn't fail
    (global_claude / "commands" / "global_cmd.md").write_text("# Global Cmd\n", encoding="utf-8")
    (project_dir / ".claude" / "commands").mkdir(parents=True)

    # Run the script with HERMES_HOME set to a non-existent directory
    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    env["PROJECT_ROOT"] = str(project_dir)
    env["HERMES_HOME"] = str(home_dir / "non_existent_hermes")
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(
        ["/bin/bash", "-x", str(EXPORT_SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    print("SOFT SKIP STDOUT:", result.stdout)
    print("SOFT SKIP STDERR:", result.stderr)

    if debug_log.is_file():
        print("SOFT SKIP DEBUG LOG:", debug_log.read_text(encoding="utf-8"))

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    # Verify it soft-skipped hermes without errors and hermes folder is not in output
    assert not (export_output / "hermes").exists()
