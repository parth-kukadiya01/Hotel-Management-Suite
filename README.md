# Hotel Review Engine - Real-Time Guest Reputation & Escalation System

A production-ready ML-powered backend service for analyzing hotel reviews in real-time using Large Language Models. Built with FastAPI, PostgreSQL, and OpenAI's GPT models.

## 🎯 Features

- **Real-Time Review Analysis**: Automated LLM-powered sentiment analysis, topic categorization, and urgency detection
- **Secure RESTful API**: JWT-based authentication with role-based access control (Staff/Manager)
- **Asynchronous Processing**: Background task management for non-blocking review ingestion
- **Critical Review Detection**: Automatic flagging of reviews requiring immediate escalation
- **Analytics Dashboard**: Comprehensive metrics including sentiment distribution, topic breakdown, and escalation rates
- **Production-Ready**: Fully containerized with Docker, comprehensive test suite, and PostgreSQL database

## 🏗️ Architecture

### Tech Stack
- **Backend Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15
- **LLM Integration**: OpenAI GPT-3.5-turbo
- **Authentication**: JWT with bcrypt password hashing
- **Containerization**: Docker & Docker Compose
- **Testing**: Pytest with async support

### Key Components
1. **Review Processing Pipeline**: Fetches reviews → LLM analysis → Database storage
2. **LLM Analyzer**: Multi-faceted analysis (sentiment, topics, urgency)
3. **Insights API**: Secure endpoints for triggering ingestion and retrieving metrics
4. **Background Task Manager**: Asynchronous task handling for long-running operations

## 📋 Prerequisites

- Docker & Docker Compose installed
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- 2GB RAM minimum
- Git

## 🚀 Quick Start

### 1. Clone the Repository
```bash