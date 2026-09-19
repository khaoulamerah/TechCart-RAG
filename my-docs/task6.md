## Task: Explore Qdrant and Build the Chunking Pipeline

### Objective

Build the foundation of the **document chunking and vector-search pipeline** for the e-commerce AI system.

The task should begin with **exploring Qdrant practically**, then comparing it with PostgreSQL and MongoDB for vector storage and retrieval, and finally using the knowledge gained to design and implement the initial chunking pipeline.

### 1. Explore Qdrant

* [ ] Set up Qdrant locally using Docker.
* [ ] Learn the core Qdrant concepts:

  * Collections
  * Vectors
  * Points
  * Payloads
  * Vector dimensions
  * Distance metrics
  * Similarity search
  * Filtering
  * Indexing
* [ ] Create a test collection.
* [ ] Insert sample vectors with metadata/payloads.
* [ ] Retrieve vectors/points.
* [ ] Perform similarity searches.
* [ ] Test filtering combined with vector search.
* [ ] Experiment with updating and deleting points.
* [ ] Explore collection configuration and indexes.
* [ ] Test different distance metrics such as cosine and Euclidean.

### 2. Compare Vector Storage Options

Research and document the differences between storing embeddings in:

* [ ] **Qdrant**
* [ ] **PostgreSQL + pgvector**
* [ ] **MongoDB Vector Search**

Compare them based on:

| Aspect                            | Qdrant | PostgreSQL + pgvector | MongoDB |
| --------------------------------- | ------ | --------------------- | ------- |
| Vector storage                    |        |                       |         |
| Similarity search                 |        |                       |         |
| Metadata filtering                |        |                       |         |
| Indexing                          |        |                       |         |
| Performance                       |        |                       |         |
| Scalability                       |        |                       |         |
| Transactions                      |        |                       |         |
| Existing relational/document data |        |                       |         |
| Operational complexity            |        |                       |         |
| Best use cases                    |        |                       |         |

The goal is not only to determine **which one is faster**, but to understand **why a dedicated vector database such as Qdrant can be preferable to storing embeddings alongside normal application data**.

### 3. Understand the Data Architecture

Define what belongs in each database.

For example:

```text
PostgreSQL
    └── Products
    └── Users
    └── Orders
    └── Inventory
    └── Categories

MongoDB
    └── Conversations
    └── AI-related document data

Qdrant
    └── Embeddings
    └── Chunk metadata
    └── Vector-search indexes
```

Determine whether Qdrant should store:

* the complete document
* only the embedding
* the chunk text
* metadata
* references to the original document

The preferred design should avoid unnecessarily duplicating large amounts of source data.

### 4. Design the Chunking Pipeline

Define the pipeline:

```text
Document
   ↓
Document Loader
   ↓
Text Extraction
   ↓
Text Cleaning
   ↓
Chunking
   ↓
Embedding Generation
   ↓
Qdrant
```

Define:

* [ ] Chunk size
* [ ] Chunk overlap
* [ ] Chunk metadata
* [ ] Document IDs
* [ ] Chunk IDs
* [ ] Embedding model
* [ ] Vector dimensions
* [ ] Distance metric
* [ ] Qdrant collection structure

A chunk should conceptually contain something similar to:

```text
Chunk
 ├── id
 ├── document_id
 ├── text
 ├── embedding
 └── metadata
      ├── source
      ├── document_type
      ├── section
      └── position
```

### 5. Implement the Initial Pipeline

* [ ] Create a reusable chunking component.
* [ ] Implement chunk generation.
* [ ] Generate embeddings for each chunk.
* [ ] Create the Qdrant collection automatically.
* [ ] Store chunks and embeddings in Qdrant.
* [ ] Implement similarity search.
* [ ] Return the most relevant chunks for a query.
* [ ] Test the complete flow with sample e-commerce documents.

### 6. Document Findings

Create technical documentation covering:

1. **What is Qdrant?**
2. **How Qdrant stores vectors**
3. **Collections, points and payloads**
4. **How similarity search works**
5. **How filtering works**
6. **Qdrant vs PostgreSQL + pgvector**
7. **Qdrant vs MongoDB Vector Search**
8. **Why the project uses Qdrant**
9. **Chunking strategy**
10. **Final vector-storage architecture**

### Definition of Done

The task is complete when:

* [ ] Qdrant runs locally.
* [ ] You can create collections and insert vectors.
* [ ] You can query vectors using similarity search.
* [ ] You understand payloads and filtering.
* [ ] You have tested updating/deleting vectors.
* [ ] You have documented Qdrant vs PostgreSQL vs MongoDB.
* [ ] The chunking strategy is defined.
* [ ] A document can be transformed into chunks.
* [ ] Chunks can be embedded.
* [ ] Embeddings can be stored in Qdrant.
* [ ] A query can retrieve the most relevant chunks.
* [ ] The architecture and design decisions are documented.
