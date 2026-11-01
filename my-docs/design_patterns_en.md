
In one sentence each:

> **Pipeline organizes. Strategy implements. Factory builds. Registry registers and retrieves.**

---

## 1. Pipeline Pattern

### Definition

A **Pipeline** breaks down a complex process into a **sequence of independent steps** (`Stage`), executed in order, where the output of one stage becomes the input of the next. The Pipeline doesn't know *what* each stage does — it only knows how to chain them.

### Simple example

```python
class Stage:
    def run(self, data):
        raise NotImplementedError

class CleanText(Stage):
    def run(self, data):
        return data.strip()

class Lowercase(Stage):
    def run(self, data):
        return data.lower()

class Pipeline:
    def __init__(self, stages: list[Stage]):
        self.stages = stages

    def run(self, data):
        for stage in self.stages:
            data = stage.run(data)
        return data

pipeline = Pipeline([CleanText(), Lowercase()])
result = pipeline.run("  HELLO WORLD  ")
# "  HELLO WORLD  " -> "HELLO WORLD" -> "hello world"
```

**What it solves**: without a Pipeline, you'd have a single `process(data)` function doing everything in one block — hard to test step by step, hard to reorder, hard to reuse partially.

---

## 2. Strategy Pattern

### Definition

**Strategy** allows **several ways of performing the same operation**, interchangeable, behind a common interface. The code that *uses* the strategy never knows which one is plugged in.

### Simple example

```python
from abc import ABC, abstractmethod

class DiscountStrategy(ABC):
    @abstractmethod
    def apply(self, price: float) -> float: ...

class NoDiscount(DiscountStrategy):
    def apply(self, price):
        return price

class TenPercentOff(DiscountStrategy):
    def apply(self, price):
        return price * 0.9

class Checkout:
    def __init__(self, discount: DiscountStrategy):
        self.discount = discount  # injected, never hardcoded

    def total(self, price: float) -> float:
        return self.discount.apply(price)

Checkout(NoDiscount()).total(100)      # 100
Checkout(TenPercentOff()).total(100)   # 90
```

**What it solves**: without Strategy, `Checkout` would contain an `if self.has_discount: ... else: ...` — every new discount rule would force a change inside `Checkout` itself.

**The right test to recognize a genuine Strategy**: do all implementations share **exactly the same input/output signature and the same business meaning**? If yes → legitimate Strategy. If not (e.g. "cleaning a CSV" vs "cleaning a Markdown" don't mean the same thing) → this is probably not a Strategy, but two different processes.

---

## 3. Factory Pattern

### Definition

A **Factory** is a function (or class) whose only role is to **build and assemble** a final object from its ingredients, so the calling code doesn't need to know the construction details.

### Simple example

```python
def create_checkout(has_discount: bool) -> Checkout:
    discount = TenPercentOff() if has_discount else NoDiscount()
    return Checkout(discount)

checkout = create_checkout(has_discount=True)
```

**What it solves**: without a Factory, every place in the code that needs a `Checkout` would have to repeat the logic of "which strategy to pick and how to assemble the object." The Factory centralizes that construction in one place.

---

## 4. Registry Pattern

### Definition

A **Registry** is a lookup table (often a dictionary) between a **name/key** and **an implementation**. Instead of an `if/elif` that keeps growing with every new case, each implementation **registers itself** under a name, and is later retrieved by that name.

### Simple example

```python
_REGISTRY: dict[str, type[DiscountStrategy]] = {}

def register(name: str):
    def decorator(cls):
        _REGISTRY[name] = cls
        return cls
    return decorator

@register("none")
class NoDiscount(DiscountStrategy):
    def apply(self, price): return price

@register("ten_percent")
class TenPercentOff(DiscountStrategy):
    def apply(self, price): return price * 0.9

def get_discount(name: str) -> DiscountStrategy:
    return _REGISTRY[name]()

get_discount("ten_percent").apply(100)  # 90
```

**What it solves**: without a Registry, adding a new strategy forces you to edit an existing Factory (`if name == "new_case": ...`). With a Registry, the new strategy adds itself — the Factory never changes.

---

## How the 4 patterns fit together in this project

```
Registry   → answers: "which class handles the 'loading' stage for the 'csv' type?"
Strategy   → answers: "how does THIS class do the loading work?"
Factory    → answers: "how do I assemble the 5 stages into a full Pipeline?"
Pipeline   → answers: "in what order do I run these 5 stages?"
```

### The registry: a grid (stage × type), not a simple list

Instead of a registry with a single key (`"csv"` → one whole bundle of strategies), we use a registry with **two keys**: `(stage_name, data_type)`. Each `Strategy` registers itself individually for the cell that concerns it:

```text
                loading              cleaning             validation           derive               save
        ┌───────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
  csv   │ CsvLoadingStrategy │ CsvCleaningStrategy│ CsvValidationStrategy│ CsvDeriveStrategy │ CsvSaveStrategy   │
        ├───────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
markdown│MarkdownLoadingStrategy│MarkdownCleaningStrategy│MarkdownValidationStrategy│MarkdownDeriveStrategy│MarkdownSaveStrategy│
        └───────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

`registry.get("loading", "csv")` → a single cell of this grid → `CsvLoadingStrategy`.

### What each pattern solves, concretely, in this project

| Pattern | Problem it solves here |
|---|---|
| **Registry** | Extensibility: adding a 3rd source type (PDF) = registering 5 new classes, **zero lines changed** in the existing code. |
| **Factory** (`create_pipeline`) | Assembly: always the same 5 stages, in the same order, **never duplicated** between `csv` and `markdown`. |
| **Strategy** | The actual behavior of each stage changes depending on the data type, without `LoadStage`/`CleanStage`/etc. needing to know which one is plugged in. |
| **Pipeline** | The execution order (`load → clean → validate → derive → save`) is defined **once**, independently of the data type being processed. |
