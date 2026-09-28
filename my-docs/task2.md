# Task 2: Chat Logic, API Integration, and Frontend Connection

## Overview

The objective of this task is to implement the complete chat workflow by connecting the frontend with the backend and integrating the Conversation module.

This version of the chat is for **unauthenticated users only**. The goal is to allow guest users to send messages, receive a **fixed testing response**, and persist conversations in MongoDB.

At the end of this task, the project should provide a **working chat UI** that communicates with the backend and saves the full conversation in the database (mongodb).

The backend must **not** connect to any LLM or external AI service. Every assistant response must always return the same message:

**"this is just a testing message of devlopment"**

**Estimated Duration:** 1–2 Days

---

# Objectives

* Build the chat API.
* Implement the chat business logic.
* Connect the Chat Service with the Conversation module.
* Support guest users only.
* Connect the frontend (HTML, CSS, JavaScript) with the backend.
* Return the same fixed assistant response for every message.
* Persist conversations in MongoDB.
* Provide a working UI that displays the testing response.

---

# Chat Flow

The complete workflow should be:

```text
User
    │
    ▼
Frontend (HTML/CSS/JS)
    │
    ▼
Chat API
    │
    ▼
Chat Service
    │
    ├── Conversation Service
    └── Static Response Generator
    │
    ▼
Save conversation
    │
    ▼
Return fixed response
    │
    ▼
Frontend
```

---

# Backend Implementation

## Chat API

Create endpoints responsible for interacting with the chat logic.

Example endpoints:

| Method | Endpoint                   | Description                           |
| ------ | -------------------------- | ------------------------------------- |
| POST   | `/chat`                    | Send a message and receive a response |
| GET    | `/chat/conversations/{id}` | Retrieve a conversation               |
| GET    | `/chat/conversations`      | List conversations                    |
| DELETE | `/chat/conversations/{id}` | Delete a conversation                 |

---

# Chat Logic

Implement the main chat workflow.

Responsibilities:

* Receive the user's message.
* Load the conversation.
* Create a new conversation if necessary.
* Build the conversation context.
* Generate the fixed assistant response.
* Save both user and assistant messages.
* Return the response to the frontend.

The assistant response must always be:

**"this is just a testing message of devlopment"**

---

# Conversation Integration

The Chat Service module must use the Conversation Service.

Responsibilities:

* Create conversations.
* Retrieve previous messages.
* Append new messages.
* Update conversation timestamps.

The Chat Service must never communicate directly with MongoDB.

---

# Guest Users

Support conversations for users who are not authenticated.

Requirements:

* Generate a unique session ID.
* Store conversations using the session ID.
* Continue the conversation while the session is valid.
* Keep the conversation available for the same browser session.
* Allow the session to be reused until it expires or is cleared.

---

# Frontend

Implement a simple chat interface using:

* HTML
* CSS
* JavaScript (Fetch API)

The interface should include:

* Chat window
* Message input
* Send button
* Loading indicator
* Error message display
* Automatic scrolling
* Display of the fixed assistant response

---

# Frontend Responsibilities

The frontend should:

* Create a new conversation when necessary.
* Send user messages to the backend.
* Display the fixed assistant response.
* Preserve the current conversation ID.
* Handle API errors gracefully.
* Update the UI after each response is received.

---

# JavaScript Logic

Implement functionality for:

* Sending messages
* Receiving responses
* Updating the chat UI
* Creating conversations
* Loading existing conversations
* Displaying loading states
* Handling network failures
* Saving and reusing the conversation ID in the browser session

---

# API Integration

Use asynchronous requests.

Example flow:

```text
User types message
        │
        ▼
POST /chat
        │
        ▼
Backend processes request
        │
        ▼
Return fixed response
        │
        ▼
Frontend updates message
        │
        ▼
Save final conversation
```

---

# Error Handling

Handle the following cases:

* Empty messages
* Invalid conversation IDs
* Expired guest sessions
* Network failures
* Internal server errors

Provide meaningful error messages to the user.

---

# Validation

Validate:

* Message length
* Conversation existence
* Session identifiers
* Request format

---

# Project Deliverables

At the end of this task, the project should provide:

* A functional chat API.
* Complete chat workflow.
* Integration between the Chat Service and Conversation modules.
* Frontend connected to the backend.
* Guest chat support only.
* Conversation persistence in MongoDB.
* A fixed assistant response for every message.
* Proper request validation and error handling.
* A working UI that displays the testing message.

---

# Acceptance Criteria

The task is complete when:

* Users can start a new conversation as guests.
* Users can continue an existing guest conversation.
* Every message receives the same fixed response.
* The frontend communicates with the backend through the API.
* The chat interface displays the assistant message correctly.
* Conversations are saved correctly in MongoDB.
* Errors are handled gracefully.
* The implementation follows the project's modular architecture.
