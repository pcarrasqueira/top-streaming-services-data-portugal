#!/usr/bin/env python3
"""
Simple test to verify the refactored code structure works correctly.
This is a basic smoke test - no external dependencies required.
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from top_pt_stream_services import Config, StreamingServiceTracker, main
    
    def test_config_initialization():
        """Test that Config class can be initialized."""
        config = Config()
        assert config.REQUEST_TIMEOUT == 30
        assert config.MAX_RETRIES == 10
        assert 'netflix' in config.urls
        assert 'movies' in config.sections
        print("✓ Config initialization test passed")
    
    def test_tracker_initialization():
        """Test that StreamingServiceTracker can be initialized."""
        tracker = StreamingServiceTracker()
        assert tracker.config is not None
        assert hasattr(tracker, 'netflix_movies_list_data')
        print("✓ StreamingServiceTracker initialization test passed")
    
    def test_main_function_exists():
        """Test that main function is callable."""
        assert callable(main)
        print("✓ Main function accessibility test passed")

    def test_run_fails_when_no_lists_are_scraped():
        """A fully failed scrape must make the workflow fail instead of updating empty lists."""
        tracker = StreamingServiceTracker()
        tracker._scrape_all_services = lambda: {"netflix_movies": []}
        assert tracker.run() == -1
        print("✓ Empty scrape failure test passed")
    
    def run_tests():
        """Run all tests."""
        print("Running refactoring tests...")
        test_config_initialization()
        test_tracker_initialization()
        test_main_function_exists()
        test_run_fails_when_no_lists_are_scraped()
        print("\n🎉 All tests passed! The refactored code structure is working correctly.")
    
    if __name__ == "__main__":
        run_tests()

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)
