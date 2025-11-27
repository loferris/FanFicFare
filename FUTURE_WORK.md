# Future Work and Known Limitations

## Transliteration Module (fanficfare/translit.py)

### Current Limitations

**Scope**: Only supports Cyrillic scripts
- Russian, Ukrainian, Belarusian, Bulgarian, Serbian
- **Crashes** on non-Cyrillic unicode (AssertionError)
- Cannot handle: Greek, Arabic, Chinese, Japanese, Korean, Hebrew, Thai, etc.

**Method**: Simple character-by-character mapping
- Uses `unicodedata.name()` to get character names
- No context-aware rules or phonetic accuracy
- No digraph handling (e.g., "щ" → "shch" is not implemented)
- Example: "Привет" → "Priviet" (should be "Privet" for accuracy)

**Error Handling**: Fails hard instead of graceful degradation
- Non-Cyrillic unicode raises AssertionError
- Should pass through unchanged or use fallback transliteration

### Recommended Improvements

#### 1. Use Existing Library (Recommended)
Replace custom implementation with battle-tested library:

**Option A: `unidecode`**
```python
from unidecode import unidecode
unidecode('北亰')  # 'Bei Jing' (Chinese)
unidecode('Κνωσός')  # 'Knosos' (Greek)
unidecode('العربية')  # "l'rby" (Arabic - less accurate)
```
- Pros: Handles 100+ scripts, well-maintained
- Cons: ASCII-only output (loses accents like é → e)

**Option B: `transliterate`**
```python
from transliterate import translit
translit('Привет', 'ru', reversed=True)  # 'Privet'
```
- Pros: Language-aware, better accuracy, reversible
- Cons: Requires language detection, more complex

**Option C: Keep simple but make robust**
```python
def romanize(letter):
    try:
        letter.encode('ascii')
        return letter
    except UnicodeEncodeError:
        pass

    try:
        unid = unicodedata.name(letter)
    except ValueError:
        return letter  # Unknown character, pass through

    # Handle special characters
    if "NUMERO SIGN" in unid:
        return "No"
    # ... other exceptions

    # Only transliterate Cyrillic, pass through everything else
    if not unid.startswith("CYRILLIC"):
        return letter  # Don't crash!

    # ... existing Cyrillic logic
```

#### 2. Add More Script Support

If keeping custom implementation:

**Greek**: Similar to Cyrillic, straightforward mapping
- Α → A, Β → B, Γ → G, Δ → D, etc.
- Pattern: `if unid.startswith("GREEK")`

**Arabic/Hebrew**: Requires RTL and vowel handling
- More complex due to right-to-left
- Consider using library for these

**CJK (Chinese/Japanese/Korean)**: Use pinyin/romanization libraries
- Chinese: `pypinyin` for pinyin conversion
- Japanese: `pykakasi` for romaji conversion
- Korean: `jamo` for romanization

#### 3. Improve Error Handling

Current: Crashes on non-Cyrillic
```python
assert(unid.startswith("CYRILLIC"))  # Dies here!
```

Better: Graceful fallback
```python
if not unid.startswith("CYRILLIC"):
    logger.debug(f"Cannot transliterate {letter} ({unid})")
    return letter  # Pass through unchanged
```

### Impact Assessment

**Current Usage**: 0% before this session (completely broken)
**Fixed Usage**: Works for Cyrillic only
**User Impact**: Low-medium
- Most fanfic sites are English, Russian, or use Latin scripts
- Chinese/Korean sites exist but may use English metadata
- Arabic fanfic sites are rare but growing

**Testing Coverage**: 97.67% for current implementation
- All Cyrillic cases tested
- Non-Cyrillic crash behavior documented in tests

---

## Cross-Language Support Analysis

### HTML Parsing

**Status**: ✅ **Well-supported**

**Evidence**:
- BeautifulSoup 4 is unicode-aware
- Handles UTF-8 encoded HTML from any language
- Tested with: Russian, Ukrainian (via transliteration tests)

**Potential Issues**:
- Character encoding detection (should use UTF-8)
- Malformed encoding declarations in HTML
- Sites serving wrong charset headers

**Test Coverage**: Limited to Latin/Cyrillic
- Should add tests for CJK character handling
- Test Arabic RTL content
- Test emoji and special unicode

### Entity Handling (htmlcleanup.py)

**Status**: ✅ **Excellent for European languages**

**Coverage**: 362+ HTML entities
- Latin with diacritics: á, é, ñ, ö, etc. ✅
- Greek letters: α, β, γ, δ ✅
- Mathematical symbols: ±, ×, ÷, ≠ ✅
- Typographic: —, ", ", « »  ✅
- Currency: €, £, ¥ ✅

**Missing**:
- CJK ideographs (usually not entities, direct unicode)
- Arabic characters (usually direct unicode)
- Modern emoji (use unicode, not entities)

**Recommendation**: Fine as-is
- Entities are mainly for Latin-based scripts
- CJK/Arabic use direct unicode characters
- EPUB supports full unicode

### EPUB Generation (epubutils.py)

**Status**: ⚠️ **Unknown - needs investigation**

**Current Coverage**: 12.09% (269/306 lines untested)

**Critical Questions**:
1. Does it specify UTF-8 encoding in EPUB manifest?
2. Are XML declarations correct for unicode?
3. Does it handle RTL (right-to-left) text direction?
4. Are font requirements specified for non-Latin scripts?

**EPUB Spec Requirements for Unicode**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Must declare UTF-8 -->

<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh">
<!-- Language declaration helps readers -->

<head>
  <meta charset="UTF-8"/>
  <!-- Redundant but safe -->
</head>
```

**RTL Support** (Arabic, Hebrew):
```html
<html dir="rtl" lang="ar">
<!-- Direction attribute -->

<style>
  body { direction: rtl; unicode-bidi: embed; }
</style>
```

**Font Embedding**:
- EPUB readers must support unicode
- Fallback fonts usually handle CJK
- Embedded fonts increase file size significantly
- Most readers have system fonts for common scripts

### Story Metadata (story.py)

**Status**: ⚠️ **Unknown - needs investigation**

**Current Coverage**: 26.61% (706/962 lines untested)

**Concerns**:
1. Are author names/titles stored as unicode strings?
2. Does metadata sorting handle non-ASCII correctly?
3. Are there string length assumptions (CJK chars = 1 char each)?
4. Date parsing for non-English date formats?

### Character Encoding Chain

**HTML Fetch → Parse → Process → EPUB**

```
1. HTTP Response
   ├─ Encoding: UTF-8 (hopefully)
   ├─ May have wrong charset header
   └─ May have BOM (byte order mark)

2. BeautifulSoup Parse
   ├─ Auto-detects encoding (usually correct)
   ├─ Converts to Python unicode strings ✅
   └─ Handles entities → unicode chars ✅

3. htmlcleanup Processing
   ├─ Entity conversion ✅
   ├─ HTML tag stripping ✅
   └─ Text normalization ✅

4. EPUB Generation
   ├─ Must declare UTF-8 ❓
   ├─ Must preserve unicode ❓
   └─ Must handle RTL ❓
```

### Known Issues from Codebase

**From configurable.py** (42% coverage):
```python
# Suggests encoding awareness exists
# But needs testing with non-Latin input
```

**From adapters**:
- 117+ site adapters
- Some may have encoding issues
- No tests for non-English sites

### Testing Gaps

**What's NOT tested**:
- [ ] Chinese/Japanese/Korean text handling
- [ ] Arabic/Hebrew RTL text
- [ ] Emoji in titles/descriptions
- [ ] Mixed-script content (e.g., English + Chinese)
- [ ] Encoding edge cases (BOM, wrong charset)
- [ ] EPUB unicode declaration
- [ ] Font fallback behavior

**Should Add**:
```python
# tests/unit/test_unicode_support.py
class TestCJKSupport:
    def test_chinese_title(self):
        html = '<title>这是一个标题</title>'
        # Parse and verify correct handling

    def test_japanese_author(self):
        html = '<author>村上春樹</author>'
        # Verify no mojibake (garbled text)

    def test_emoji_in_description(self):
        text = "Great story! 😊👍"
        # Ensure emoji preserved in EPUB

class TestRTLSupport:
    def test_arabic_text_direction(self):
        text = "مرحبا"  # "Hello" in Arabic
        # Verify RTL handling
```

### Recommendations

#### Immediate (Low-hanging fruit):
1. ✅ **Fix transliteration crash** - Done! Now passes through
2. **Add unicode test cases** - Chinese, Arabic, emoji
3. **Audit EPUB encoding** - Check UTF-8 declarations
4. **Test RTL handling** - Add Arabic/Hebrew test stories

#### Medium-term (Weeks 4-5):
1. **Increase EPUB test coverage** - Currently 12%, need 60%+
2. **Test story metadata with CJK** - Author names, titles
3. **Verify adapter encoding handling** - Spot-check popular non-English sites
4. **Add encoding error recovery** - Graceful degradation

#### Long-term (Phase 1 completion):
1. **Replace transliteration** - Use `unidecode` library
2. **Add language detection** - For better transliteration
3. **Embedded font support** - For rare scripts
4. **RTL CSS generation** - Auto-detect and apply direction

### Impact on Current Work

**For Week 3 Testing**:
- Focus on modules with UTF-8 handling
- Add unicode test cases where possible
- Document encoding assumptions

**For Week 5 Modernization**:
- Type hints should use `str` (unicode in Py3)
- Don't add ASCII encoding restrictions
- Preserve unicode throughout pipeline

### Real-World Test Cases

**Should manually test with**:
1. Russian fanfic: https://ficbook.net/ (Cyrillic)
2. Chinese fanfic: https://www.jjwxc.net/ (Simplified Chinese)
3. Korean fanfic: https://www.munpia.com/ (Hangul)
4. Japanese fanfic: https://syosetu.com/ (Kanji/Kana)
5. Arabic fanfic: (if supported sites exist)

**Expected Behavior**:
- ✅ Download works (UTF-8 preserved)
- ✅ EPUB renders correctly in readers
- ⚠️ Transliteration fails gracefully (non-Cyrillic)
- ❌ May have issues with RTL text direction

---

## Priority Assessment

**High Priority** (Blocks users):
- ✅ Transliteration crashes - FIXED

**Medium Priority** (Degrades experience):
- [ ] EPUB unicode declaration audit
- [ ] RTL text direction support
- [ ] Transliteration library upgrade

**Low Priority** (Nice to have):
- [ ] Font embedding for rare scripts
- [ ] Advanced language detection
- [ ] Phonetically accurate transliteration

**Testing Priority**:
1. Add CJK test cases (Week 3/4)
2. Test EPUB generation (Week 4)
3. Manual testing with non-English sites (Week 6)
