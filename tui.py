import os
import math
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Grid
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Footer, Tree, Label
from textual.widgets.tree import TreeNode

class ConfirmDialog(ModalScreen):
    """A modal dialog to confirm an action."""

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Grid(
            Static(self.message, id="dialog_message"),
            Button("Yes", variant="primary", id="yes"),
            Button("No", variant="default", id="no"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")

class DuplicateFinderApp(App):
    """A Textual app to manage duplicate files."""

    CSS_PATH = "tui.css"
    BINDINGS = [
        ("delete", "toggle_delete", "Mark/Unmark"),
        ("f10", "commit_deletions", "Commit Deletions"),
        ("q", "request_quit", "Quit"),
        ("escape", "request_quit", "Quit"),
    ]

    def __init__(self, duplicates):
        super().__init__()
        self.duplicates = duplicates
        self.marked_for_deletion = set()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        keys_header = "Keys: [↑/↓] Navigate | [Tab] Switch Sort | [Enter] Apply | [Del] Mark/Unmark | [F10] Commit Deletions | [Esc] Quit"
        yield Static(keys_header, id="keys_header")
        with Horizontal(id="sort_toolbar"):
            yield Label("Sort by:")
            yield Button("By Total Size", id="sort_by_size")
            yield Button("By File Count", id="sort_by_count")
        tree = Tree("Duplicate Files")
        tree.show_root = False
        yield tree
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.sort_duplicates("size")
        self.repopulate_tree()
        self.update_footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when a button is pressed."""
        if event.button.id == "sort_by_size":
            self.sort_duplicates("size")
        elif event.button.id == "sort_by_count":
            self.sort_duplicates("count")
        self.repopulate_tree()

    def sort_duplicates(self, by: str) -> None:
        """Sorts the duplicates list and updates button variants."""
        if by == "size":
            self.duplicates.sort(key=lambda item: os.path.getsize(item[1][0]) * len(item[1]) if item[1] else 0, reverse=True)
        elif by == "count":
            self.duplicates.sort(key=lambda item: len(item[1]), reverse=True)

        self.query_one("#sort_by_size").variant = "primary" if by == "size" else "default"
        self.query_one("#sort_by_count").variant = "primary" if by == "count" else "default"

    def repopulate_tree(self) -> None:
        """Clears and repopulates the Tree with duplicate file data."""
        tree = self.query_one(Tree)
        tree.clear()
        for checksum, paths in self.duplicates:
            if paths:
                try:
                    size = os.path.getsize(paths[0])
                    total_size = size * len(paths)
                    formatted_size = self.format_size(total_size)
                    basename = os.path.basename(paths[0])
                    group_label = f"▼ {formatted_size}, {len(paths)} files: '{basename}'"
                    group_node = tree.root.add(group_label, data={"type": "group", "paths": paths})
                    for path in sorted(paths):
                        label = f"[DELETE] {path}" if path in self.marked_for_deletion else path
                        group_node.add_leaf(label, data={"type": "file", "path": path})
                except (FileNotFoundError, IndexError):
                    continue
        tree.root.expand_all()

    def action_toggle_delete(self) -> None:
        """Toggles the deletion status of the selected file."""
        tree = self.query_one(Tree)
        node = tree.cursor_node

        if not node or node.data.get("type") != "file":
            return

        path = node.data["path"]
        group_node = node.parent
        all_paths_in_group = set(group_node.data["paths"])

        if path in self.marked_for_deletion:
            self.marked_for_deletion.remove(path)
            node.label = path
        else:
            marked_in_group = all_paths_in_group.intersection(self.marked_for_deletion)
            if len(marked_in_group) < len(all_paths_in_group) - 1:
                self.marked_for_deletion.add(path)
                node.label = f"[DELETE] {path}"
            else:
                footer = self.query_one(Footer)
                footer.text = "Cannot mark the last file in a group for deletion."
                self.set_timer(2, self.update_footer)
                return

        self.update_footer()

    def action_commit_deletions(self) -> None:
        """Commits the deletion of marked files after confirmation."""
        if not self.marked_for_deletion:
            footer = self.query_one(Footer)
            footer.text = "No files to delete."
            self.set_timer(2, self.update_footer)
            return

        count = len(self.marked_for_deletion)
        plural = "s" if count > 1 else ""
        message = f"Permanently delete {count} file{plural}?"

        def on_confirm(confirmed: bool) -> None:
            if confirmed:
                self.delete_files()

        self.push_screen(ConfirmDialog(message), on_confirm)

    def action_request_quit(self) -> None:
        """Requests to quit the application, confirming if there are unsaved changes."""
        if not self.marked_for_deletion:
            self.exit()
        else:
            message = "You have files marked for deletion. Are you sure you want to quit?"
            def on_confirm(confirmed: bool) -> None:
                if confirmed:
                    self.exit()

            self.push_screen(ConfirmDialog(message), on_confirm)

    def delete_files(self) -> None:
        """Performs the actual file deletion and updates the UI."""
        deleted_count = 0
        for path in self.marked_for_deletion:
            try:
                os.remove(path)
                deleted_count += 1
            except OSError:
                pass

        footer = self.query_one(Footer)
        plural = "s" if deleted_count > 1 else ""
        footer.text = f"Deleted {deleted_count} file{plural}."

        self.marked_for_deletion.clear()
        self.update_duplicates_list()
        self.repopulate_tree()
        self.set_timer(3, self.update_footer)

    def update_duplicates_list(self) -> None:
        """Removes deleted files from the internal duplicates list."""
        new_duplicates = []
        for checksum, paths in self.duplicates:
            remaining_paths = [p for p in paths if os.path.exists(p)]
            if len(remaining_paths) > 1:
                new_duplicates.append((checksum, remaining_paths))
        self.duplicates = new_duplicates

    def update_footer(self) -> None:
        """Updates the footer with the count and size of marked files."""
        count = len(self.marked_for_deletion)
        footer = self.query_one(Footer)
        if count == 0:
            footer.text = "No files marked for deletion."
        else:
            total_size = sum(os.path.getsize(path) for path in self.marked_for_deletion if os.path.exists(path))
            formatted_size = self.format_size(total_size)
            plural = "s" if count > 1 else ""
            footer.text = f"Status: {count} file{plural} marked for deletion ({formatted_size}). Press F10 to commit."

    def format_size(self, size_bytes: int) -> str:
        """Formats a size in bytes to a human-readable string."""
        if size_bytes == 0:
            return "0B"
        try:
            size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
            i = int(math.floor(math.log(size_bytes, 1024)))
            p = math.pow(1024, i)
            s = round(size_bytes / p, 2)
            return f"{s} {size_name[i]}"
        except ValueError:
            return "0B"
