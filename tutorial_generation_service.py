import json
import subprocess
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


def slugify(value: str) -> str:
    import re

    value = (value or "").strip().lower()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_-]+", "-", value)
    return value or "tutorial"


@dataclass
class TutorialTask:
    task_id: str
    description: str
    output_dir: Path
    status: str = "queued"
    created_at: float = field(default_factory=lambda: __import__("time").time())
    updated_at: float = field(default_factory=lambda: __import__("time").time())
    log: str = ""
    options: Dict = field(default_factory=dict)
    return_code: Optional[int] = None


class TutorialGenerationService:
    """
    Simple background task runner that spawns launch_planning.py for each request.
    """

    def __init__(self, repo_root: Path, results_base: Optional[Path] = None):
        self.repo_root = Path(repo_root)
        self.results_base = Path(results_base or (self.repo_root / "results" / "tutorial_tasks"))
        self.results_base.mkdir(parents=True, exist_ok=True)
        self.tasks: Dict[str, TutorialTask] = {}
        self.lock = threading.Lock()

    def submit_task(self, description: str, options: Optional[Dict] = None) -> TutorialTask:
        task_id = uuid.uuid4().hex[:12]
        slug = slugify(description)[:40]
        task_output_dir = self.results_base / f"{slug}-{task_id}"
        task_output_dir.mkdir(parents=True, exist_ok=True)

        task = TutorialTask(
            task_id=task_id,
            description=description,
            output_dir=task_output_dir,
            options=options or {},
        )

        with self.lock:
            self.tasks[task_id] = task

        thread = threading.Thread(target=self._run_task, args=(task,), daemon=True)
        thread.start()
        return task

    def get_task(self, task_id: str) -> Optional[TutorialTask]:
        with self.lock:
            return self.tasks.get(task_id)

    def list_tasks(self) -> Dict[str, TutorialTask]:
        with self.lock:
            return dict(self.tasks)

    # Internal
    def _run_task(self, task: TutorialTask) -> None:
        task.status = "running"
        task.updated_at = __import__("time").time()
        cmd = self._build_command(task)

        try:
            completed = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            task.return_code = completed.returncode
            task.log = (completed.stdout or "") + "\n" + (completed.stderr or "")
            if completed.returncode == 0:
                task.status = "success"
            else:
                task.status = "failed"
        except Exception as exc:  # pylint: disable=broad-except
            task.status = "failed"
            task.log = f"Tutorial generation crashed: {exc}"
            task.return_code = -1
        finally:
            task.updated_at = __import__("time").time()
            self._write_status_file(task)

    def _build_command(self, task: TutorialTask):
        description = task.description
        opts = task.options or {}
        script_path = self.repo_root / "launch_planning.py"
        cmd = [
            "python3",
            str(script_path),
            "--text-input",
            description,
            "--non_interactive",
            "--auto_survey",
            "--enable_judger",
            "--enable_review",
            "--output_dir",
            str(task.output_dir),
            "--max_rounds",
            str(opts.get("max_rounds", 2)),
        ]
        if opts.get("max_papers"):
            cmd += ["--max_papers", str(opts["max_papers"])]
        if opts.get("skip_literature_summary", True):
            cmd.append("--skip_literature_summary")
        if opts.get("description_override"):
            cmd += ["--description", opts["description_override"]]
        if opts.get("target_audience"):
            cmd += ["--target_audience", opts["target_audience"]]
        if opts.get("min_clarity_score"):
            cmd += ["--min_clarity_score", str(opts["min_clarity_score"])]
        if opts.get("min_coherence_score"):
            cmd += ["--min_coherence_score", str(opts["min_coherence_score"])]
        return cmd

    def _write_status_file(self, task: TutorialTask):
        status_path = task.output_dir / "task_status.json"
        payload = {
            "task_id": task.task_id,
            "description": task.description,
            "status": task.status,
            "return_code": task.return_code,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "output_dir": str(task.output_dir),
        }
        try:
            status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:  # pylint: disable=broad-except
            pass

