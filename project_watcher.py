import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import project_scanner
import gdscript_scanner
import scene_scanner
import build_index
import project_graph


GODOT_PROJECT = Path(r"C:\Users\berke\OneDrive\Desktop\silicon_frontier")


WATCHED_EXTENSIONS = {
    ".gd",
    ".tscn",
    ".tres",
    ".godot",
}


class ProjectChangeHandler(FileSystemEventHandler):

    def on_any_event(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)

        if path.suffix.lower() not in WATCHED_EXTENSIONS:
            return

        print(f"\nChange detected: {path}")

        rebuild_indexes()


def rebuild_indexes():
    print("Rebuilding project index...")

    project_scanner.scan_project(GODOT_PROJECT)
    gdscript_scanner.main()
    scene_scanner.main()

    build_index.main()

    index = project_graph.load_index()
    project_graph.build_graph(index)

    print("Project index updated.\n")


def main():
    print("Godot project watcher started.")
    print(f"Watching: {GODOT_PROJECT}")

    observer = Observer()
    handler = ProjectChangeHandler()

    observer.schedule(
        handler,
        str(GODOT_PROJECT),
        recursive=True,
    )

    observer.start()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping watcher...")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()