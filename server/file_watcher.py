#!/usr/bin/env python3
"""
File Watcher - Hot Reload for Document Changes
===============================================
Uses watchdog to monitor /my_documents/ for changes and automatically re-index.
Creates seamless auto-save loop where vector brain mirrors folder perfectly.

NO manual refresh needed - changes are detected and indexed in real-time.
"""

import time
import threading
from pathlib import Path
from typing import Callable, Optional
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileModifiedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
)


class DocumentEventHandler(FileSystemEventHandler):
    """
    Handles file system events for document directory.
    Triggers re-indexing when files are modified, created, or deleted.
    """

    def __init__(self, on_change_callback: Callable, documents_dir: Path):
        """
        Initialize event handler.

        Args:
            on_change_callback: Function to call when file changes
            documents_dir: Directory being watched
        """
        super().__init__()
        self.on_change = on_change_callback
        self.documents_dir = documents_dir
        self.debounce_timer: Optional[threading.Timer] = None
        self.debounce_seconds = 2.0  # Wait 2 seconds after last change

    def _trigger_reindex(self, file_path: Path):
        """
        Trigger re-indexing with debouncing to avoid multiple rapid updates.

        Args:
            file_path: Path to changed file
        """
        # Cancel previous timer if exists
        if self.debounce_timer:
            self.debounce_timer.cancel()

        # Set new timer
        self.debounce_timer = threading.Timer(
            self.debounce_seconds, self.on_change, args=[file_path]
        )
        self.debounce_timer.start()

    def on_modified(self, event):
        """Handle file modification events"""
        if isinstance(event, FileModifiedEvent):
            file_path = Path(event.src_path)
            if self._is_relevant_file(file_path):
                print(f"\n📝 File modified: {file_path.name}")
                self._trigger_reindex(file_path)

    def on_created(self, event):
        """Handle file creation events"""
        if isinstance(event, FileCreatedEvent):
            file_path = Path(event.src_path)
            if self._is_relevant_file(file_path):
                print(f"\n✨ File created: {file_path.name}")
                self._trigger_reindex(file_path)

    def on_deleted(self, event):
        """Handle file deletion events"""
        if isinstance(event, FileDeletedEvent):
            file_path = Path(event.src_path)
            if self._is_relevant_file(file_path):
                print(f"\n🗑️  File deleted: {file_path.name}")
                self._trigger_reindex(file_path)

    def _is_relevant_file(self, file_path: Path) -> bool:
        """
        Check if file is relevant for indexing.

        Args:
            file_path: Path to check

        Returns:
            True if file should be indexed
        """
        # Skip hidden files and directories
        if file_path.name.startswith("."):
            return False

        # Skip temporary files
        if file_path.suffix in [".tmp", ".swp", ".bak", "~"]:
            return False

        # Only index supported file types
        supported_extensions = [
            ".pdf",
            ".docx",
            ".xlsx",
            ".pptx",
            ".html",
            ".md",
            ".txt",
        ]
        return file_path.suffix.lower() in supported_extensions


class LocalFileWatcher:
    """
    Watches document directory for changes and triggers re-indexing.
    Runs in background thread without blocking main application.
    """

    def __init__(
        self,
        documents_dir: str = "./my_documents",
        on_change_callback: Optional[Callable] = None,
    ):
        """
        Initialize file watcher.

        Args:
            documents_dir: Directory to watch
            on_change_callback: Function to call when files change
        """
        self.documents_dir = Path(documents_dir)
        self.documents_dir.mkdir(parents=True, exist_ok=True)

        self.on_change_callback = on_change_callback or self._default_callback
        self.observer: Optional[Observer] = None
        self.is_running = False

        # Create event handler
        self.event_handler = DocumentEventHandler(
            self.on_change_callback, self.documents_dir
        )

        print("✅ File Watcher initialized")
        print(f"   📁 Watching: {self.documents_dir}")

    def _default_callback(self, file_path: Path):
        """Default callback when file changes"""
        print(f"   🔄 Re-indexing: {file_path.name}")

    def start(self):
        """Start watching for file changes"""
        if self.is_running:
            print("⚠️  File watcher already running")
            return

        # Set up observer
        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            str(self.documents_dir),
            recursive=True,  # Watch subdirectories too
        )

        # Start observer thread
        self.observer.start()
        self.is_running = True

        print("👁️  File watcher started (watching for changes...)")

    def stop(self):
        """Stop watching for file changes"""
        if not self.is_running:
            return

        self.observer.stop()
        self.observer.join()
        self.is_running = False

        print("⏹️  File watcher stopped")

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


# Global instance
_file_watcher: Optional[LocalFileWatcher] = None


def start_file_watcher(
    documents_dir: str = "./my_documents", on_change_callback: Optional[Callable] = None
) -> LocalFileWatcher:
    """
    Start file watcher in background.

    Args:
        documents_dir: Directory to watch
        on_change_callback: Function to call on file changes

    Returns:
        File watcher instance
    """
    global _file_watcher

    if _file_watcher and _file_watcher.is_running:
        print("⚠️  File watcher already running")
        return _file_watcher

    _file_watcher = LocalFileWatcher(documents_dir, on_change_callback)
    _file_watcher.start()

    return _file_watcher


def stop_file_watcher():
    """Stop file watcher"""
    global _file_watcher
    if _file_watcher:
        _file_watcher.stop()
        _file_watcher = None


def get_watcher_status() -> dict:
    """
    Get file watcher status.

    Returns:
        Dictionary with status information
    """
    global _file_watcher

    if _file_watcher and _file_watcher.is_running:
        return {
            "status": "running",
            "watching": str(_file_watcher.documents_dir),
            "message": "✅ Watching for file changes",
        }
    else:
        return {
            "status": "stopped",
            "watching": None,
            "message": "⏹️  File watcher not running",
        }


if __name__ == "__main__":
    # Test file watcher
    print("🚀 Testing File Watcher")
    print("=" * 60)

    def test_callback(file_path: Path):
        print(f"   🔄 Callback triggered: {file_path.name}")
        print("      (In production, this would re-index the file)")

    # Start watcher
    watcher = start_file_watcher("./my_documents", test_callback)

    print(f"\n📁 Test directory: {watcher.documents_dir}")
    print("👁️  Watching for changes...")
    print("\n💡 To test:")
    print(f"   1. Create/modify a file in: {watcher.documents_dir}")
    print("   2. Watch for re-indexing callback")
    print("   3. Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping file watcher...")
        stop_file_watcher()
        print("✅ Done")
