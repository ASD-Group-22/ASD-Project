# Student 2 - Skill Exchange Service - Release 0

## Overview

The Skill Exchange Service allows students to create listings for skills they can offer and skills they want to learn.

The service can identify compatible exchange partners using stored listing and availability data. AI Mode uses application evidence to rank and explain suitable matches while preventing the model from inventing students, listings, skills, or availability.

## Architecture

```text
Browser
  ↓
Nginx frontend microservice
  ↓ HTTP
Flask backend/API microservice
  ├─→ Student 2 database API → SQLite
  ├─→ Skill Profile Service API, when available
  └─→ Ollama → Qwen main model → Llama review model