# Task 1: MongoDB Integration and Conversation CRUD

## Overview

The objective of this task is to introduce MongoDB into the project and implement the data access layer for managing chat conversations and the messages stored inside them.

At the end of this task, the project should be able to connect to MongoDB and perform complete CRUD operations on the **Conversation** collection, including embedded **Message** documents, using the **Repository Pattern** and **Service Layer** in FastAPI.

**Estimated Duration:** 03 Day

---

# Objectives

* Learn the fundamentals of MongoDB.
* Set up MongoDB using Docker.
* Integrate MongoDB into the FastAPI project.
* Design the Conversation document with embedded messages.
* Implement CRUD operations for conversations.
* Implement message management inside conversations.
* Follow a clean architecture using the Repository Pattern.

---

# Learning Phase

Before implementation, spend some time understanding the following MongoDB concepts.

## MongoDB Fundamentals

Study:

* Databases
* Collections
* Documents
* BSON
* ObjectId

## CRUD Operations

Learn how to:

* Insert documents
* Query documents
* Update documents
* Delete documents

## Embedded Documents and Arrays

Understand how MongoDB stores nested data, especially:

* Embedded documents
* Arrays of subdocuments
* Updating nested array items
* Querying nested fields

This is important because messages will be stored inside each conversation document.

## Indexes

Understand how indexes improve query performance.

For this task, create indexes for:

* `_id`
* `session_id`
* `user_id`
* `created_at`

## Docker

Learn how to:

* Run MongoDB inside Docker
* Persist data using Docker volumes
* Configure MongoDB using environment variables

---

# Docker Setup

Create a Docker configuration for MongoDB.

Requirements:

* MongoDB container
* Persistent volume
* Environment variables
* Authentication enabled
* Local development support

The database should be accessible by the FastAPI application through environment variables.

---

# Conversation Model

Create a MongoDB document representing a conversation.

Each conversation should contain its own embedded list of messages.

Suggested fields:

| Field      | Type          | Description                                                |
| ---------- | ------------- | ---------------------------------------------------------- |
| id         | ObjectId      | MongoDB document identifier                                |
| session_id | String        | Guest session identifier                                   |
| user_id    | String | None | Authenticated user identifier                              |
| title      | String        | Conversation title                                         |
| is_guest   | Boolean       | Indicates whether the conversation belongs to a guest user |
| messages   | Array         | Embedded list of message documents                         |
| created_at | DateTime      | Creation timestamp                                         |
| updated_at | DateTime      | Last update timestamp                                      |
| metadata   | Dictionary    | Additional conversation metadata                           |

## Message Subdocument

Each message stored inside a conversation should follow a structure similar to the following:

| Field      | Type            | Description                                        |
| ---------- | --------------- | -------------------------------------------------- |
| message_id | ObjectId/String | Unique identifier for the embedded message         |
| role       | String          | Message sender role, such as `user` or `assistant` |
| content    | String          | Message text                                       |
| created_at | DateTime        | Message creation timestamp                         |
| metadata   | Dictionary      | Additional message metadata                        |

## Notes

* `user_id` is optional because guests can use the chatbot without authentication.
* Every conversation must have a unique `session_id`.
* Guest conversations can later be linked to an authenticated user.
* Messages are stored inside the conversation document as embedded subdocuments.
* Each message should have a unique identifier within its conversation.

---

# Project Structure

The implementation should follow the Repository Pattern.

```text
.
│
├── database/
│   └── mongodb.py
│
├── models/
│   └── conversation.py
│
├── repositories/
│   └── conversation.py
│
├── services/
│   └── conversation.py
│
└── routers/
    └── conversation.py
```

---

# Repository Layer

The repository layer is responsible only for interacting with MongoDB.

It must not contain any business logic.

## Responsibilities

Implement methods for:

### Create Conversation

Create a new conversation document.

### Get By ID

Retrieve a conversation using its MongoDB identifier.

### Get By Session ID

Retrieve a conversation using its session identifier.

### Get By User ID

Return all conversations belonging to a user.

### List Conversations

Return conversations with pagination.

### Update Conversation

Update conversation information.

### Delete Conversation

Delete a conversation.

### Add Message

Append a new embedded message to a conversation.

### Get Messages

Return all messages from a conversation.

### Update Message

Update a specific embedded message inside a conversation.

### Delete Message

Remove a specific embedded message from a conversation.

---

# Service Layer

The service layer contains the application's business logic.

It should communicate only with the repository layer.

## Responsibilities

### Create Conversation

* Validate the request.
* Generate timestamps.
* Call the repository.

### Get Conversation

* Verify that the conversation exists.
* Return the conversation.

### List Conversations

* Handle pagination parameters.
* Return paginated results.

### Update Conversation

* Validate editable fields.
* Update timestamps.
* Save changes through the repository.

### Delete Conversation

* Verify that the conversation exists.
* Remove it using the repository.

### Add Message

* Validate the message payload.
* Generate message identifiers and timestamps.
* Append the message to the conversation.

### Get Messages

* Verify that the conversation exists.
* Return the embedded messages.

### Update Message

* Verify that the conversation and message exist.
* Validate editable fields.
* Update the embedded message.

### Delete Message

* Verify that the conversation and message exist.
* Remove the embedded message from the conversation.

---

# API Endpoints

Implement the following REST endpoints.

## Conversation Endpoints

| Method | Endpoint              | Description              |
| ------ | --------------------- | ------------------------ |
| POST   | `/conversations`      | Create a conversation    |
| GET    | `/conversations/{id}` | Get a conversation by ID |
| GET    | `/conversations`      | List conversations       |
| PUT    | `/conversations/{id}` | Update a conversation    |
| DELETE | `/conversations/{id}` | Delete a conversation    |

## Message Endpoints

| Method | Endpoint                                    | Description                            |
| ------ | ------------------------------------------- | -------------------------------------- |
| POST   | `/conversations/{id}/messages`              | Add a message to a conversation        |
| GET    | `/conversations/{id}/messages`              | List all messages in a conversation    |
| PUT    | `/conversations/{id}/messages/{message_id}` | Update a message inside a conversation |
| DELETE | `/conversations/{id}/messages/{message_id}` | Delete a message from a conversation   |

---

# Validation

The implementation should include:

* Request validation using Pydantic
* Response models
* Proper HTTP status codes
* Error handling for invalid IDs and missing conversations
* Error handling for missing embedded messages
* Validation of message roles and content

---

# Coding Guidelines

The implementation should follow these principles:

* Repository Pattern
* Service Layer Pattern
* Dependency Injection
* Asynchronous FastAPI endpoints
* Async MongoDB driver
* Type hints
* Environment-based configuration
* Clear separation of concerns

The API layer must never communicate directly with MongoDB. All database operations should go through the repository, and all business rules should be implemented in the service layer.

Because messages are stored inside conversations, all message operations must be handled through the conversation repository and conversation service.

---

# Deliverables

At the end of this task, the following should be completed:

* MongoDB running in Docker.
* MongoDB successfully integrated with FastAPI.
* Conversation model implemented with embedded messages.
* Message subdocument model implemented.
* Repository layer implemented.
* Service layer implemented.
* REST API exposing complete CRUD operations for conversations.
* REST API exposing message management inside conversations.
* Project structured according to the Repository Pattern and ready for implementing advanced chat features in the next task.
