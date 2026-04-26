import json
from engine.timeline_model import TimelineProject

class ProjectManager:
    def __init__(self):
        self.project = TimelineProject()
        self.undo_stack = []
        self.redo_stack = []

    def save_project(self, path):
        with open(path, 'w') as f:
            json.dump(self.project.to_dict(), f, indent=2)

    def load_project(self, path):
        with open(path, 'r') as f:
            data = json.load(f)
            self.project = TimelineProject.from_dict(data)
            self.undo_stack.clear()
            self.redo_stack.clear()

    def push_state(self):
        self.undo_stack.append(self.project.to_dict())
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            state = self.undo_stack.pop()
            # swap with current
            current = self.project.to_dict()
            self.redo_stack.append(current)
            self.project = TimelineProject.from_dict(state)
            return True
        return False

    def redo(self):
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(self.project.to_dict())
            self.project = TimelineProject.from_dict(state)
            return True
        return False