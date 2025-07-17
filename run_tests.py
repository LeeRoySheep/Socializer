import unittest
from datamanager.test_data_model import TestDataModel
import unittest
import sys
import os

def run_tests():
    # Make sure the package is importable
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

    # Discover and run tests
    test_suite = unittest.defaultTestLoader.discover('datamanager', pattern='test_*.py')
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    # Exit with appropriate code
    return 0 if result.wasSuccessful() else 1
#!/usr/bin/env python
import unittest
import sys
import os

def run_tests():
    # Add the current directory to the path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'datamanager')
    suite = loader.discover(start_dir, pattern='test_*.py')

    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())
if __name__ == "__main__":
    sys.exit(run_tests())
if __name__ == "__main__":
    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDataModel)

    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)

    # Print summary
    print(f"Tests run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")

    # Exit with appropriate code
    import sys
    sys.exit(not result.wasSuccessful())
