#!/usr/bin/env python
"""
Test runner for AgentOps multi-session tests.
Provides configuration and detailed reporting for test execution.

Usage:
    python run_tests.py [options]

Options:
    --mode          Test mode: unit, integration, concurrent, all (default: all)
    --verbose       Verbose output (default: False)
    --report        Generate HTML report (default: False)
    --parallel      Run tests in parallel (default: False)
    --failfast      Stop on first failure (default: False)
"""

import pytest
import argparse
import sys
import os
from datetime import datetime
from typing import List, Optional
from pathlib import Path

def setup_python_path():
    """Add necessary directories to Python path."""
    # Get the project root directory (parent of tests directory)
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    # Add src directory to Python path
    sys.path.insert(0, str(src_dir))
    
    # Add project root to Python path
    sys.path.insert(0, str(project_root))
    
    if os.environ.get("PYTHONPATH"):
        print(f"PYTHONPATH: {os.environ['PYTHONPATH']}")
    print(f"sys.path: {sys.path}")

class TestRunner:
    """Manages test execution and reporting."""
    
    def __init__(self, mode: str = "all", verbose: bool = False,
                 report: bool = False, parallel: bool = False,
                 failfast: bool = False):
        self.mode = mode
        self.verbose = verbose
        self.report = report
        self.parallel = parallel
        self.failfast = failfast
        self.test_dir = Path(__file__).parent
        self.results_dir = self.test_dir / "results"
        
    def setup(self):
        """Prepare test environment."""
        # Create results directory if needed
        self.results_dir.mkdir(exist_ok=True)
        
        # Set up test markers based on mode
        self.test_markers = {
            "unit": "not integration and not concurrent",
            "integration": "integration",
            "concurrent": "concurrent",
            "all": None
        }
        
        # Set up Python path
        setup_python_path()
    
    def get_pytest_args(self) -> List[str]:
        """Build pytest arguments based on configuration."""
        args = [
            str(self.test_dir / "test_multi_session.py"),
            "-v" if self.verbose else "",
            "--tb=short",
            f"-n {os.cpu_count()}" if self.parallel else "",
            "--maxfail=1" if self.failfast else "",
            # Add pythonpath to pytest
            f"--import-mode=importlib",
        ]
        
        # Add test selection based on mode
        if self.mode != "all":
            args.append(f"-m '{self.test_markers[self.mode]}'")
            
        # Add HTML report generation
        if self.report:
            report_path = self.results_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            args.extend(["--html", str(report_path)])
            
        return [arg for arg in args if arg]  # Remove empty strings
    
    def run(self) -> int:
        """Run tests and return exit code."""
        self.setup()
        
        print(f"\n{'='*80}")
        print(f"Running AgentOps Multi-Session Tests")
        print(f"Mode: {self.mode}")
        print(f"{'='*80}\n")
        
        args = self.get_pytest_args()
        
        if self.verbose:
            print("pytest arguments:", " ".join(args))
            
        return pytest.main(args)
    
    def generate_report(self, exit_code: int):
        """Generate test execution report."""
        if not self.report:
            return
            
        # Additional custom reporting logic can be added here
        report_file = self.results_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, "w") as f:
            f.write(f"Test Execution Summary\n")
            f.write(f"=====================\n")
            f.write(f"Date: {datetime.now().isoformat()}\n")
            f.write(f"Mode: {self.mode}\n")
            f.write(f"Exit Code: {exit_code}\n")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run AgentOps multi-session tests")
    parser.add_argument("--mode", choices=["unit", "integration", "concurrent", "all"],
                       default="all", help="Test execution mode")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--report", action="store_true",
                       help="Generate HTML report")
    parser.add_argument("--parallel", action="store_true",
                       help="Run tests in parallel")
    parser.add_argument("--failfast", action="store_true",
                       help="Stop on first failure")
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    runner = TestRunner(
        mode=args.mode,
        verbose=args.verbose,
        report=args.report,
        parallel=args.parallel,
        failfast=args.failfast
    )
    
    exit_code = runner.run()
    runner.generate_report(exit_code)
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
