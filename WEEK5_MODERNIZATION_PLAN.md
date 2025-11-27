# Week 5: Modernization Plan

## Strategy

**Principle**: Modernize modules with high test coverage first, so we can verify nothing breaks.

**Order of Modernization** (by test coverage):
1. ✅ exceptions.py - 100% coverage (30 tests) - COMPLETE
2. ✅ HtmlTagStack.py - 100% coverage (43 tests) - COMPLETE
3. ✅ translit.py - 100% coverage (43 tests) - COMPLETE (improved from 97.67%)
4. ✅ dateutils.py - 97.26% coverage (31 tests) - COMPLETE
5. ✅ htmlcleanup.py - 93.26% coverage (46 tests) - COMPLETE (improved from 86.92%)
6. ⏳ Other modules as coverage increases

## Week 5 Status: COMPLETE ✅

All 5 target modules fully modernized with:
- Comprehensive type hints on all functions
- Google-style docstrings with examples
- Removal of all Python 2 compatibility code
- Modern Python patterns (f-strings, proper exception handling)
- Zero test regressions (193 tests passing)
- Coverage improvements across the board

## Modernization Checklist

For each module:

### 1. Add Type Hints
- [ ] Function signatures with `->` return types
- [ ] Parameter types
- [ ] Class attributes with types
- [ ] Use `from typing import List, Dict, Optional, Union` etc.

### 2. Remove Python 2 Compatibility
- [ ] Remove `from __future__ import absolute_import`
- [ ] Remove `from .six import ...` where possible
- [ ] Replace `basestring` with `str`
- [ ] Replace `unicode` with `str`
- [ ] Use f-strings instead of `%` formatting or `.format()`
- [ ] Use `//` for integer division (explicit)

### 3. Improve Code Quality
- [ ] Add docstrings (Google or NumPy style)
- [ ] Simplify complex conditionals
- [ ] Extract magic numbers to constants
- [ ] Use context managers (`with` statements)
- [ ] Use comprehensions where clearer

### 4. Modern Python Patterns
- [ ] Use `pathlib.Path` instead of `os.path` (where appropriate)
- [ ] Use `dataclasses` for data structures (where appropriate)
- [ ] Use `enum.Enum` for constants (where appropriate)
- [ ] Use `@property` decorators
- [ ] Type guards with `isinstance()` or type hints

### 5. Error Handling
- [ ] Specific exception types
- [ ] Clear error messages
- [ ] Proper exception chaining (`from e`)
- [ ] Remove bare `except:` clauses

### 6. Testing After Each Change
- [ ] Run module-specific tests
- [ ] Verify coverage unchanged or improved
- [ ] Run full test suite
- [ ] Commit small, atomic changes

## Example: Modernizing exceptions.py

### Before:
```python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .six import text_type as unicode

class FailedToDownload(Exception):
    def __init__(self,error):
        self.error = error
    def __str__(self):
        return unicode(self.error)
```

### After:
```python
"""Custom exception classes for FanFicFare errors."""

from typing import Optional


class FailedToDownload(Exception):
    """Raised when story download fails.

    Attributes:
        error: Description of the download failure
    """

    def __init__(self, error: str) -> None:
        """Initialize with error message.

        Args:
            error: Description of what failed
        """
        self.error = error
        super().__init__(error)

    def __str__(self) -> str:
        """Return error message as string."""
        return str(self.error)
```

## Modernization Phases

### Phase 1: Type Hints (Low Risk)
Start with adding type hints without changing logic.
- Adds static type checking capability
- Doesn't change runtime behavior
- Easy to verify with tests

### Phase 2: Remove Six (Medium Risk)
Replace six compatibility with Python 3 native.
- Some risk of breaking edge cases
- Well-tested with our test suite
- Clear wins in readability

### Phase 3: Refactor (Higher Risk)
Improve code structure and patterns.
- Requires careful testing
- Do incrementally
- Focus on well-tested modules first

## Success Metrics

After modernization, each module should have:
- ✅ Type hints on all public functions
- ✅ Python 3.8+ syntax (no Python 2 compat)
- ✅ Docstrings on public API
- ✅ All tests still passing
- ✅ No decrease in coverage
- ✅ Improved readability

## Tools to Use

**Type Checking:**
```bash
pip install mypy
mypy fanficfare/exceptions.py
```

**Code Quality:**
```bash
pip install pylint
pylint fanficfare/exceptions.py
```

**Auto-formatting:**
```bash
pip install black
black fanficfare/exceptions.py --line-length 100
```

**Import Sorting:**
```bash
pip install isort
isort fanficfare/exceptions.py
```

## Risk Mitigation

**Safety Net:**
- 225 passing tests (93 from adapters, 132 from utilities)
- 23.13% overall coverage (but 85-100% on modernized modules)
- Run tests after EVERY change
- Commit frequently with clear messages

**Rollback Strategy:**
- Git commits for each logical change
- Can revert individual commits if issues found
- Test suite will catch regressions immediately

## Timeline Estimate

**Per Module:**
- Small module (40-100 lines): 30-60 minutes
- Medium module (100-300 lines): 1-2 hours
- Large module (300+ lines): 2-4 hours

**Week 5 Goals:**
- Modernize 5 well-tested modules (exceptions, HtmlTagStack, translit, dateutils, htmlcleanup)
- Estimated time: 6-10 hours
- Add type hints to 3-5 additional modules
- Update documentation for modernization patterns

## Python Version Target

**Minimum: Python 3.8**
- Supports modern type hints
- Still widely used
- Balances new features with compatibility

**Features We Can Use:**
- Type hints with `->` and `:` syntax ✅
- f-strings ✅
- `pathlib.Path` ✅
- `dataclasses` ✅
- Walrus operator `:=` (optional)
- Dictionary merge `|` operator (optional)
- Match statements (Python 3.10+) - skip for now

## Example Session

**Modernizing exceptions.py:**

1. **Read current code** ✅
2. **Add type hints** (10 min)
   - Function signatures
   - Attributes
   - Run tests ✅
   - Commit
3. **Remove six imports** (5 min)
   - Replace `unicode` with `str`
   - Remove `from __future__ import`
   - Run tests ✅
   - Commit
4. **Add docstrings** (15 min)
   - Module docstring
   - Class docstrings
   - Run tests ✅
   - Commit
5. **Improve error messages** (10 min)
   - Use f-strings
   - Add context
   - Run tests ✅
   - Commit
6. **Final verification** (5 min)
   - Run full test suite
   - Check coverage
   - Create summary commit

**Total: ~45 minutes per module**

## Let's Start!

First module to modernize: **exceptions.py**
- 100% test coverage (30 tests)
- Simple exception classes
- Clear, contained scope
- Perfect starter module
