"""
Simple progress indicator for WorkspaceAI

Provides a clean, minimalist progress indicator using dots to show
when the AI is thinking or performing tasks.
"""

import sys
import time
import threading
from typing import Optional

class ProgressIndicator:
    """Simple progress indicator using dots"""
    
    def __init__(self, message: str = "", max_dots: int = 3, interval: float = 0.5):
        """
        Initialize progress indicator
        
        Args:
            message: Text to show before the dots (empty for dots only)
            max_dots: Maximum number of dots to show before cycling
            interval: Time between dot updates in seconds
        """
        self.message = message
        self.max_dots = max_dots
        self.interval = interval
        self.running = False
        self.thread = None
        self._dot_count = 0
        
    def start(self):
        """Start the progress indicator"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop the progress indicator and clear the line"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        
        # Clear the progress line
        sys.stdout.write('\r' + ' ' * (len(self.message) + self.max_dots + 2) + '\r')
        sys.stdout.flush()
        
    def _run(self):
        """Internal method to run the progress animation"""
        while self.running:
            # Create dots string
            dots = '.' * self._dot_count
            padding = ' ' * (self.max_dots - self._dot_count)
            
            # Write the progress line - just dots if no message
            if self.message:
                sys.stdout.write(f'\r{self.message}{dots}{padding}')
            else:
                sys.stdout.write(f'\r{dots}{padding}')
            sys.stdout.flush()
            
            # Update dot count
            self._dot_count = (self._dot_count + 1) % (self.max_dots + 1)
            
            # Wait for next update
            time.sleep(self.interval)
            
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


class SimpleProgress:
    """Ultra-simple progress indicator - just dots"""
    
    def __init__(self, message: str = ""):
        self.message = message
        self.active = False
        
    def show(self):
        """Show the progress message"""
        if not self.active:
            if self.message:
                sys.stdout.write(f'{self.message}...')
            else:
                sys.stdout.write('...')
            sys.stdout.flush()
            self.active = True
            
    def hide(self):
        """Hide the progress message"""
        if self.active:
            # Clear the line
            if self.message:
                clear_length = len(self.message) + 3
            else:
                clear_length = 3
            sys.stdout.write('\r' + ' ' * clear_length + '\r')
            sys.stdout.flush()
            self.active = False
            
    def __enter__(self):
        """Context manager entry"""
        self.show()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.hide()


# Convenience functions for easy use
def show_progress(message: str = "", animated: bool = True, max_dots: int = 3, interval: float = 0.5):
    """
    Create and return a progress indicator
    
    Args:
        message: Text to show before the dots (empty for dots only)
        animated: Whether to animate the dots or show static
        max_dots: Maximum number of dots for animation
        interval: Time between updates for animation
        
    Returns:
        Progress indicator context manager
    """
    if animated:
        return ProgressIndicator(message, max_dots, interval)
    else:
        return SimpleProgress(message)
