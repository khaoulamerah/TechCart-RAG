
# Running the Same Software Multiple Times with Docker

## Table of Contents

1. Introduction
2. Running Software Natively vs Docker
3. Running the Same Software Multiple Times
4. Docker Isolation
5. Case Study: Ollama
6. Running Multiple Ollama Containers
7. Host + Docker Combination
8. Port Mapping
9. Exposing Multiple Containers
10. Reverse Proxy
11. Load Balancing
12. Software Replication
13. Running Multiple Instances vs Replication
14. Practical Architectures
15. Best Practices
16. Summary


# Introduction

One of Docker's biggest advantages is the ability to run **multiple isolated instances of exactly the same application** on a single machine.

Unlike traditional installations, Docker packages the application together with its dependencies, configuration, and runtime environment inside an isolated container.

This makes it possible to run:

* Different versions
* Different configurations
* Independent data
* Independent networking

all on the same host without conflicts.


# Running Software Natively

Suppose you install Ollama directly on Linux.

```
sudo pacman -S ollama
```

or

```
curl -fsSL https://ollama.com/install.sh | sh
```

The result is

```
Host
│
└── Ollama
      Port 11434
```

The service listens on

```
localhost:11434
```

Trying to start another Ollama process usually results in

```
Error:
Port already in use
```

because only one process can bind to the same IP and port combination.


# Running Software with Docker

Docker provides isolation.

Instead of installing Ollama directly on the host, every container has its own

* filesystem
* network stack
* process space
* environment variables

Example:

```
Host
│
├── Container A
│      Ollama
│
├── Container B
│      Ollama
│
└── Container C
       Ollama
```

Each container thinks it is the only Ollama installation.


# Why Does This Work?

Inside each container:

```
localhost:11434
```

exists independently.

Container A

```
127.0.0.1:11434
```

Container B

```
127.0.0.1:11434
```

Container C

```
127.0.0.1:11434
```

Although the port number is identical, each container owns its own network namespace.


> so we can conclude that etch container has its own internal network...

# Case Study: Ollama

The official image:

```bash
docker pull ollama/ollama
```

Run one container:

```bash
docker run -d \
    --name ollama1 \
    -p 11434:11434 \
    ollama/ollama
```

Architecture

```
Host:11434
      │
      ▼
Container
┌──────────────┐
│ Ollama       │
│ Port 11434   │
└──────────────┘
```


# Running Multiple Ollama Containers

Create another one.

```bash
docker run -d \
    --name ollama2 \
    -p 11435:11434 \
    ollama/ollama
```

Now

```
Host

11434 ──► Container 1
             11434

11435 ──► Container 2
             11434
```

Notice that:

Inside containers

```
11434
```

Outside

```
11434
11435
```

Docker translates requests automatically.


# Running Three Containers

```bash
docker run -d --name ollama1 -p 11434:11434 ollama/ollama

docker run -d --name ollama2 -p 11435:11434 ollama/ollama

docker run -d --name ollama3 -p 11436:11434 ollama/ollama
```

Access them using

```
http://localhost:11434

http://localhost:11435

http://localhost:11436
```

Each server is completely independent.


# Host Installation + Docker Containers

A very common scenario is:

```
Host
│
├── Native Ollama
│      Port 11434
│
├── Docker Container
│      Port 11434
│
└── Docker Container
       Port 11434
```

Can this work?

Yes.

But only if host ports are different.

Example

Native installation

```
Host

11434
```

Docker

```
docker run -p 11435:11434
```

Docker

```
docker run -p 11436:11434
```

Result

```
Host

11434 -> Native Ollama

11435 -> Docker Container A

11436 -> Docker Container B
```

No conflicts occur because the host ports are unique.


# What Happens if Two Services Use the Same Host Port?

Example

```
Native Ollama

11434
```

Docker

```
-p 11434:11434
```

Docker immediately reports:

```
Bind for 0.0.0.0:11434 failed

Address already in use
```

because the host cannot assign the same port to two different services.


# Docker Port Mapping

Syntax

```text
HOST_PORT : CONTAINER_PORT
```

Example

```bash
-p 8080:80
```

means

```
Host 8080

↓

Container 80
```

For Ollama

```bash
-p 11435:11434
```

means

```
localhost:11435

↓

Container:11434
```


# Container Networking

Every container receives its own IP.

Example

```
Container A

172.17.0.2

Container B

172.17.0.3

Container C

172.17.0.4
```

Inside Docker's bridge network they can communicate directly.


# Exposing Multiple Containers

There are several approaches.

## Method 1 — Different Ports

```
localhost:11434

localhost:11435

localhost:11436
```

Simple and common for development.


## Method 2 — Reverse Proxy

Instead of remembering many ports:

```
ollama1.local

ollama2.local

ollama3.local
```

using

* Traefik
* Nginx
* HAProxy

Example

```
Internet

      │

Nginx
|
├── /gpu1 → Ollama 1
├── /gpu2 → Ollama 2
└── /gpu3 → Ollama 3
```

## Method 3 — K8s service
but we will not cover this here.

# Sharing Models Between Containers

By default every Ollama container stores its own models.

```
Container A

llama3

Container B

llama3

Container C

llama3
```

This wastes disk space.

A better solution is using a Docker volume.

```bash
docker volume create ollama-models
```

Run

```bash
docker run \
-v ollama-models:/root/.ollama \
ollama/ollama
```

Now every container can access the same downloaded models (provided your use case permits shared storage and concurrent access).


# Running Multiple Instances

Many beginners think this is replication.

It is not.

Running multiple instances simply means

```
Instance A

Instance B

Instance C
```

They are unrelated.

Each has

* its own memory
* its own configuration
* its own state
* its own storage (unless shared explicitly)

If one crashes,

the others continue running.


# What is Replication?

Replication means creating multiple copies of a service **that together provide a single logical service**.

The goal is usually

* High Availability
* Scalability
* Fault Tolerance
* Load Distribution

Instead of users selecting which instance to contact, a system distributes requests automatically.

Example

```
Users

      │

Load Balancer

│
├── Replica 1
├── Replica 2
├── Replica 3
```

The replicas provide the same service and are treated as interchangeable.


# Docker Containers vs Replication

## Running Multiple Containers

```
User

├── Container 1
├── Container 2
└── Container 3
```

The user chooses which container to use.

Example

```
localhost:11434

localhost:11435

localhost:11436
```

No automatic traffic distribution.


## Replication

```
Users

↓

Load Balancer

↓

Replica 1

Replica 2

Replica 3
```

The user sees only one endpoint.

The infrastructure chooses the replica.


# Example with Ollama

Without replication

```
Client

↓

11434

or

11435

or

11436
```

The client decides.


With replication

```
Client

↓

api.company.com

↓

Load Balancer

↓

Ollama Replica A

Ollama Replica B

Ollama Replica C
```

The client has no knowledge of individual replicas.


# Docker Compose Example

```yaml
services:

  ollama1:
    image: ollama/ollama
    ports:
      - "11434:11434"

  ollama2:
    image: ollama/ollama
    ports:
      - "11435:11434"

  ollama3:
    image: ollama/ollama
    ports:
      - "11436:11434"
```

This runs three independent Ollama containers.


# Practical Use Cases

Running multiple independent instances:

* Testing different Ollama versions
* Running different models
* Development and experimentation
* Isolated environments
* Performance benchmarking

Replication:

* AI APIs
* Production inference servers
* High availability
* Horizontal scaling
* Fault tolerance
* Load balancing


# Best Practices

* Use unique host ports for each container.
* Use Docker volumes to persist models and configuration.
* Use meaningful container names (e.g., `ollama-gpu1`, `ollama-gpu2`).
* Place containers on a dedicated Docker network if they need to communicate.
* Use a reverse proxy or an API gateway when exposing multiple instances externally.
* Use replication (with tools such as Docker Swarm or Kubernetes) when you need scalability, automatic recovery, or load balancing rather than simply running several independent containers.


# Summary

| Running Multiple Containers          | Replication                                              |
| ------------------------------------ | -------------------------------------------------------- |
| Independent instances                | Copies of the same service working together              |
| User selects the instance            | Load balancer or orchestrator selects the replica        |
| Different exposed ports are common   | Usually exposed through a single endpoint                |
| Separate lifecycle and configuration | Managed as one logical application                       |
| Ideal for testing and isolation      | Ideal for production, scalability, and high availability |

The key distinction is that **running multiple containers** is simply creating several isolated instances of the same software, while **replication** is an architectural pattern in which those instances operate as a coordinated service behind a single entry point, typically managed by an orchestrator such as Kubernetes.
