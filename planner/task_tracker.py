# Line 1:  Import enum for defining task state constants in a type-safe way.
from enum import Enum


# Line 2:  Define the TaskState enumeration with all possible states a subtask can be in.
class TaskState(Enum):
    # Line 3:  PENDING — task has been planned but not yet started.
    PENDING = "pending"
    # Line 4:  IN_PROGRESS — task is currently being executed.
    IN_PROGRESS = "in_progress"
    # Line 5:  DONE — task completed successfully with a result.
    DONE = "done"
    # Line 6:  FAILED — task encountered an error and could not complete.
    FAILED = "failed"


# Line 7:  Define the TaskTracker class that manages the lifecycle of all subtasks in a plan.
class TaskTracker:
    # Line 8:  Initialize with an empty list of tasks (populated after planning).
    def __init__(self):
        # Line 9:  Store tasks as a list of dicts, each with id, description, state, and result.
        self.tasks = []

    # Line 10:  Add a new task to the tracker in PENDING state; returns the task ID.
    def add_task(self, description):
        # Line 11:  Generate a sequential ID based on current task count (simple counter).
        task_id = len(self.tasks) + 1
        # Line 12:  Create the task dict with initial state PENDING and no result yet.
        task = {
            "id": task_id,
            "description": description,
            "state": TaskState.PENDING,
            "result": None,
        }
        # Line 13:  Append the new task to our list.
        self.tasks.append(task)
        # Line 14:  Return the task ID for reference in logging and reporting.
        return task_id

    # Line 15:  Mark a task as IN_PROGRESS (called before executing it).
    def start(self, task_id):
        # Line 16:  Find the task by ID and update its state to IN_PROGRESS.
        self._get_task(task_id)["state"] = TaskState.IN_PROGRESS

    # Line 17:  Mark a task as DONE with a result value (called after successful execution).
    def complete(self, task_id, result):
        # Line 18:  Find the task and set state to DONE, storing the result.
        task = self._get_task(task_id)
        # Line 19:  Set the state to DONE.
        task["state"] = TaskState.DONE
        # Line 20:  Store the execution result for later reference (e.g., by subsequent tasks).
        task["result"] = result

    # Line 21:  Mark a task as FAILED with an error message (called when execution raises).
    def fail(self, task_id, error_msg):
        # Line 22:  Find the task and set state to FAILED with the error description.
        task = self._get_task(task_id)
        # Line 23:  Set the state to FAILED.
        task["state"] = TaskState.FAILED
        # Line 24:  Store the error message as the result (for debugging and reporting).
        task["result"] = f"ERROR: {error_msg}"

    # Line 25:  Get the next PENDING task to execute; returns None if all tasks are done/failed.
    def get_next_pending(self):
        # Line 26:  Iterate through tasks in order to find the first one still in PENDING state.
        for task in self.tasks:
            # Line 27:  If this task is pending, return it (FIFO execution order).
            if task["state"] == TaskState.PENDING:
                # Line 28:  Return the next pending task dict.
                return task
        # Line 29:  No pending tasks remain; return None to signal completion.
        return None

    # Line 30:  Get a summary of all task states (for reporting and evaluation).
    def summary(self):
        # Line 31:  Count tasks in each state for the summary statistics.
        counts = {"pending": 0, "in_progress": 0, "done": 0, "failed": 0}
        # Line 32:  Iterate over all tasks to tally their states.
        for task in self.tasks:
            # Line 33:  Increment the count for this task's current state.
            counts[task["state"].value] += 1
        # Line 34:  Return the counts dict as the summary.
        return counts

    # Line 35:  Internal helper: find a task by its ID; raises ValueError if not found.
    def _get_task(self, task_id):
        # Line 36:  Iterate through tasks to find the one with matching ID.
        for task in self.tasks:
            # Line 37:  If IDs match, return this task dict.
            if task["id"] == task_id:
                # Line 38:  Return the found task.
                return task
        # Line 39:  Task ID not found — raise an error (shouldn't happen in normal flow).
        raise ValueError(f"Task {task_id} not found")
