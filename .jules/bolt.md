## 2024-05-24 - [Avoid Pandas Vectorized String Operations on Tiny Arrays]
**Learning:** While `df.columns.astype(str).str.lower()` is faster for large datasets (e.g., 1000+ columns), it is actually a micro-deoptimization for typical DataFrames with few columns. The overhead of pandas' `.str` accessor dispatch and Index object creation outweighs the raw iteration speed of a simple Python list comprehension `[str(c).lower() for c in df.columns]`.
**Action:** Do not replace list comprehensions with pandas vectorized string accessors when the array size is known to be very small (like DataFrame columns), unless the number of columns is explicitly known to be massive.

### 2024-06-18
- **Learned from cli/main.py**: When iterating to cross-reference keys between a static mapping (e.g. `REPORT_SECTIONS`) and a dynamic payload (e.g. `report_sections`), it can be twice as fast to iterate over the static `.items()` and use `.get(key)` on the payload. Iterating directly over the dynamic payload and performing multiple membership checks (`if section not in self.REPORT_SECTIONS`) or dictionary index lookups (`self.REPORT_SECTIONS[section]`) introduces measurable redundancy.
