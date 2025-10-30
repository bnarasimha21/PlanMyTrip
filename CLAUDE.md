# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PlanMyTrip is an AI-powered travel planning application with React/TypeScript frontend and FastAPI/Python backend. The system uses agent-based architecture (LangGraph workflow) for intelligent trip planning with interactive maps and conversational AI.

## Commands

### Frontend (React + Vite + TypeScript)
- **Development**: `cd frontend && npm run dev` (runs on port 5173)
- **Build**: `cd frontend && npm run build`
- **Preview**: `cd frontend && npm run preview --port 5174`
- **Testing**: `cd frontend && npm test` (Playwright)
- **Test UI**: `cd frontend && npm run test:ui`

### Backend (FastAPI + Python)
- **Development**: `cd backend && source venv/bin/activate && python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000`
- **Testing**: `cd backend && source venv/bin/activate && pytest`
- **Dependencies**: `cd backend && pip install -r requirements.txt`

## Architecture

### Backend Agent System
The backend uses a modular agent-based architecture powered by LangGraph:

- **Base Agent** (`agents/base_agent.py`): Core agent functionality and OpenAI integration
- **Workflow** (`agents/simple_workflow.py`): Main LangGraph workflow orchestrating all agents
- **Extraction Agent**: Parses natural language trip requests into structured data
- **Itinerary Agent**: Generates detailed travel itineraries with geocoded places
- **Search Agent**: Handles place search and recommendations
- **Question Agent**: Powers the conversational AI chatbot
- **Intent Classifier**: Routes user requests to appropriate handlers

### API Endpoints
- `POST /extract`: Extract trip details from natural language
- `POST /itinerary`: Generate complete itinerary with places and coordinates
- `POST /modify`: Modify existing itineraries through conversation
- `POST /tts`: Generate audio narration (optional GTTS integration)

### Frontend Components
Single-page React app (`frontend/src/App.tsx`) with three main panels:
- **Left Panel**: Trip request input (text)
- **Center Panel**: Interactive Mapbox map with custom markers and popups
- **Right Panel**: Itinerary display and AI chatbot interface

### Key Technologies
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Mapbox GL JS
- **Backend**: FastAPI, LangGraph, OpenAI GPT-4o-mini, GTTS, Mapbox Geocoding
- **Testing**: Playwright (frontend), pytest (backend)

## Environment Setup

### Required Environment Variables
- **Backend** (`.env`):
  - `OPENAI_API_KEY`: OpenAI API key for AI agents
  - `MAPBOX_API_KEY`: Mapbox token for geocoding
- **Frontend** (`.env`):
  - `VITE_MAPBOX_TOKEN`: Mapbox token for map display
  - `VITE_API_BASE`: Backend URL (default: http://localhost:8000)

### Development Setup
1. Backend: Create virtual environment, install requirements.txt, configure .env
2. Frontend: Run `npm install`, configure .env with Mapbox token
3. Run both servers concurrently for development

## Code Patterns

### Backend
- All agents inherit from `BaseAgent` class
- Workflow coordination through LangGraph state management
- Pydantic models for request/response validation
- Async/await patterns for API endpoints

### Frontend
- Single App.tsx component with React hooks for state management
- Mapbox integration with custom marker styling and popups
- Real-time map updates when itinerary changes

## Testing
- Frontend uses Playwright for end-to-end testing
- Backend uses pytest for unit and integration tests
- No specific linting commands configured - uses TypeScript compiler checking