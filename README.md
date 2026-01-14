# Family Assistant - Personal AI Automation Platform

## Project Overview

**Family Assistant** is a personal AI assistant built around a Telegram bot, designed to automate everyday workflows and notifications using AI, asynchronous backend services, and external integrations.

The project is actively used in production for personal needs and serves as a modular foundation for AI-driven automation, notifications, and integrations.

---

## Key Features

- **Telegram-based AI Assistant**
  - Natural language interaction
  - Context-aware responses
  - Asynchronous message handling

- **Local LLM Integration (Ollama)**
  - Self-hosted AI model running on a private home server
  - No dependency on external cloud LLM providers
  - Full control over data and privacy

- **Amazon Seller Integration**
  - Order notifications
  - Shipment updates
  - Review alerts
  - Event-driven processing using AWS services

- **Real-time Notifications**
  - Push notifications via Telegram
  - Context-based routing and filtering

- **Async-first Architecture**
  - Non-blocking IO
  - Background workers
  - Event listeners and queues

---

## High-Level Architecture

The system is composed of several loosely coupled components:

- **Telegram Bot**
  - Primary user interface
  - Handles user commands and messages
  - Sends notifications and AI-generated responses

- **Backend API**
  - Async service layer
  - Business logic and orchestration
  - Integration routing

- **AI Layer**
  - Ollama-based LLM hosted on a private server
  - Used for conversational logic and assistant behavior

- **Amazon Integration Layer**
  - Amazon Selling Partner API (SP-API)
  - AWS SQS for event notifications
  - Background listeners for order and review events

- **Storage Layer**
  - Persistent storage for users, tokens, and metadata
  - Integration-specific token isolation

---

## Architecture Principles

- **Async-first design**
  - All external I/O operations are non-blocking
  - Optimized for high-latency APIs (Telegram, Amazon, AI inference)

- **Separation of Concerns**
  - Bot logic, business logic, and integrations are isolated
  - Clean boundaries between services

- **Event-driven Communication**
  - Amazon events processed asynchronously
  - Background workers decoupled from user interactions

- **Extensibility**
  - New integrations can be added without impacting core components
  - Designed as a personal automation platform rather than a single-purpose bot

---

## Technology Stack

### Backend
- Python
- Async ASGI-based frameworks

### AI / LLM
- Ollama (self-hosted)

### Messaging
- Telegram Bot API

### Amazon Services
- Amazon Selling Partner API (SP-API)
- AWS SQS
- AWS IAM

### Storage
- SQL-based persistent storage
- Integration-specific token storage

### Infrastructure
- Self-hosted AI (home server)
- Cloud-based integrations
- Container-friendly design

---

## Security & Best Practices

- OAuth-based authorization for third-party services
- Secure token storage (no secrets in repository)
- Least-privilege access model (AWS IAM scopes)
- Clear separation between public interfaces and internal services

---

## Real-World Use Cases

- Personal AI assistant via Telegram
- Amazon seller operational monitoring
- Real-time sales, shipment, and review notifications
- Foundation for family-level automation and integrations

---

## Project Status

This project is **actively used and maintained** as a personal automation platform.  
Features and integrations evolve based on real-world usage.

---
