# Pipeline Design Pattern

## Overview

The **Pipeline Pattern** is a software design pattern used to process data through a sequence of independent processing stages.

Each stage receives an input, performs one specific operation, and passes its result to the next stage.

```text
Input
  ↓
Stage 1
  ↓
Stage 2
  ↓
Stage 3
  ↓
Output
```

The main idea is to divide a complex data-processing operation into small, reusable steps.

---

## Basic Structure

A pipeline consists of three main concepts:

### 1. Pipeline

The pipeline coordinates the execution of the stages.

```python
class Pipeline:
    def __init__(self, stages):
        self.stages = stages

    def run(self, data):
        for stage in self.stages:
            data = stage.run(data)

        return data
```

### 2. Stage

A stage performs one operation on the data.

```python
class Stage:
    def run(self, data):
        raise NotImplementedError
```

Example:

```python
class CleanText(Stage):
    def run(self, data):
        return data.strip()
```

Another stage:

```python
class Lowercase(Stage):
    def run(self, data):
        return data.lower()
```

### 3. Data

The data flows from one stage to another.

```text
"  HELLO WORLD  "
        ↓
     CleanText
        ↓
   "HELLO WORLD"
        ↓
     Lowercase
        ↓
   "hello world"
```

---

## Example

A data-cleaning pipeline could be:

```python
pipeline = Pipeline([
    CleanText(),
    Lowercase(),
    RemoveDuplicates(),
    ValidateData(),
])
```

Running it:

```python
result = pipeline.run(data)
```

The execution becomes:

```text
data
 ↓
CleanText
 ↓
Lowercase
 ↓
RemoveDuplicates
 ↓
ValidateData
 ↓
result
```

---

## Why Use the Pipeline Pattern?

### Separation of Responsibilities

Each stage should have one responsibility.

Instead of:

```python
def process_data(data):
    clean()
    validate()
    transform()
    chunk()
    store()
```

we create independent stages:

```text
Clean
Validate
Transform
Chunk
Store
```

This makes the system easier to understand and maintain.

### Reusability

Stages can be reused in different pipelines.

```python
clean = CleanText()

pipeline_a = Pipeline([
    clean,
    ChunkText(),
])

pipeline_b = Pipeline([
    clean,
    ValidateText(),
])
```

### Composability

Stages can be combined in different ways to create different pipelines.

```text
Pipeline A:

Input → Clean → Validate → Store


Pipeline B:

Input → Clean → Chunk → Embed → Store
```

### Testability

Each stage can be tested independently.

```python
def test_clean_text():
    stage = CleanText()

    result = stage.run("  hello  ")

    assert result == "hello"
```

---

## Pipeline vs Stage

These concepts should not be confused.

**Stage**:

> Performs one processing operation.

**Pipeline**:

> Connects and executes multiple stages.

```text
              Pipeline
                  │
        ┌─────────┼─────────┐
        ↓         ↓         ↓
      Stage     Stage     Stage
        ↓         ↓         ↓
      Clean    Validate   Chunk
```

---

## Pipeline and Chain of Responsibility

The Pipeline Pattern is related to the **Chain of Responsibility** pattern because both pass something through a sequence of components.

However, their intent is different.

### Pipeline

The output of one stage normally becomes the input of the next stage:

```text
A → B → C → D
```

This is particularly suitable for:

* Data processing
* ETL
* Text processing
* Document processing
* Machine-learning preprocessing

### Chain of Responsibility

The main idea is that a request passes through handlers until one of them handles it.

```text
Request
   ↓
Handler A ──→ handled?
   ↓ no
Handler B ──→ handled?
   ↓ no
Handler C
```

For a data-processing library, the **Pipeline Pattern** is usually the more natural abstraction.

---

## Design Principles

A good pipeline should follow these principles:

### Single Responsibility

Each stage should do one thing.

```text
CleanText       → cleaning
ValidateData    → validation
ChunkDocument   → chunking
```

Avoid stages that do everything:

```python
class EverythingStage:
    ...
```

### Loose Coupling

Stages should not depend heavily on other stages.

A stage should generally care about:

```text
Input → Processing → Output
```

rather than knowing which specific stage comes before or after it.

### Composition Over Complexity

Build complex behavior by composing simple stages.

```python
Pipeline([
    LoadData(),
    CleanData(),
    ValidateData(),
    TransformData(),
    StoreData(),
])
```

---

## Application in `data_pipelines`

The pattern can form the core architecture of the project:

```text
                  Pipeline
                     │
     ┌───────────────┼────────────────┐
     ↓               ↓                ↓
  Ingestion       Processing        Output
     │               │                │
     ↓               ↓                ↓
   CSV/API       Cleaning         Parquet
   Database      Validation       Database
   JSON          Transform        Vector DB
                 Chunking
```

Different implementations can then be provided for individual stages.

For example:

```text
Chunking
├── FixedSizeChunker
├── SentenceChunker
├── RecursiveChunker
└── TokenChunker
```

This is where the **Strategy Pattern** can complement the Pipeline Pattern.

---

## Summary

The Pipeline Pattern provides a simple way to structure data processing as a sequence of independent stages.

```text
Input
  ↓
Stage
  ↓
Stage
  ↓
Stage
  ↓
Output
```

Its main benefits are:

* **Separation of responsibilities**
* **Reusability**
* **Composability**
* **Testability**
* **Maintainability**

For `data_pipelines`, the Pipeline Pattern can serve as the **core execution model**, while patterns such as **Strategy**, **Adapter**, and **Dependency Injection** can be introduced where they solve specific problems.
