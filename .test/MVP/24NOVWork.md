# SFD Project Refactoring Work Plan

## Overview
This document outlines the plan to address code quality issues identified in the SFD (Shipping Fraud Detection) project. The primary focus is on improving maintainability, reducing redundancy, and eliminating potential bugs across SFD.py, SFD_GUI.py, and advanced_analysis.py.

## High-Priority Tasks

### 1. Create Shared Utilities Module (utils.py)
- Move duplicate functions to a central location
- Standardize implementations
- Functions to migrate:
  - `get_cache_dir()`
  - `check_dependencies()`
  - `format_file_size()`
  - `log_memory_usage()`
  - `validate_config()`

### 2. Remove Orphaned/Redundant Code
- Delete commented-out duplicate of `get_files_for_date_range()` (SFD.py lines 863-928)
- Identify and remove any other dead code paths
- Consolidate similar functions with different implementations

### 3. Fix Global State Management
- Replace global coordinate variables (GLOBAL_MIN_LAT, GLOBAL_MAX_LAT, etc.) with proper parameter passing
- Create a MapCoordinateManager class to handle map boundaries
- Pass coordinates as function parameters instead of using global state

## Medium-Priority Tasks

### 4. Standardize Error Handling
- Create consistent error handling patterns
- Implement helper functions for common error scenarios
- Ensure proper user notification for critical errors
- Add appropriate context in error messages

### 5. Address Threading Issues
- Add proper synchronization for resources accessed by multiple threads
- Use ThreadPoolExecutor for better thread management
- Ensure thread-safe access to shared data
- Add proper exception handling in threaded code

### 6. Improve Resource Management
- Ensure all file operations use proper context managers (`with` statements)
- Add cleanup in `finally` blocks for operations that don't use context managers
- Implement proper resource release patterns

### 7. Refactor Import Management
- Standardize optional dependency handling
- Create a centralized import checking system
- Consolidate duplicate import logic across files

## Low-Priority Tasks

### 8. Improve Code Organization
- Organize functions by category/purpose within files
- Add better module-level documentation
- Standardize function parameter naming conventions

### 9. Enhance Configurability
- Create a dedicated Config class to replace dictionary-based configuration
- Implement better default handling
- Add validation for configuration values

### 10. Code Testing
- Add unit tests for critical functions
- Create integration tests for major workflows
- Implement test fixtures for common test scenarios

## Implementation Approach

### Phase 1: Utilities Module & Code Cleanup (Days 1-2)
1. Create utils.py with core shared functions
2. Remove redundant/orphaned code
3. Update imports in all files to use the new utilities

### Phase 2: State Management & Error Handling (Days 3-4)
1. Implement proper state management for map coordinates
2. Standardize error handling across codebase
3. Improve resource management patterns

### Phase 3: Threading & Import Handling (Days 5-6)
1. Address threading safety issues
2. Improve import management system
3. Fix any remaining code organization issues

### Phase 4: Testing & Documentation (Day 7)
1. Add tests for critical functionality
2. Enhance documentation
3. Final review and cleanup

## Success Criteria
- No duplicate code between files
- No orphaned/unused code
- Consistent error handling patterns
- Thread-safe access to shared resources
- Proper resource management
- Clean, well-documented imports
- Improved maintainability and readability

This plan addresses all identified issues while prioritizing tasks that reduce immediate risks (redundancy, state management) before tackling more general improvements.
