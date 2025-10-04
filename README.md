# 🌟 AI Story Generator - Enhanced Version

<div align="center">
  <img src="https://img.shields.io/badge/Next.js-14.2.3-black?style=for-the-badge&logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/TypeScript-5.4.5-blue?style=for-the-badge&logo=typescript" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Python-3.11+-green?style=for-the-badge&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-Latest-orange?style=for-the-badge" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Tailwind-3.4.4-38B2AC?style=for-the-badge&logo=tailwind-css" alt="Tailwind" />
</div>

<div align="center">
  <h3>✨ AI-powered personalized story generation for children ✨</h3>
  <p>An interactive web application that generates personalized stories for kids using advanced AI models</p>
</div>

---
# 🚀 AI Story Generator 🎨

Welcome to the AI Story Generator, a full-stack application that brings your story ideas to life with the power of generative AI! This tool allows users to input a simple prompt and receive a complete story, enhanced with custom-generated images and even comic strips.

This document provides all the information you need to get the application running, understand its architecture, and start developing new features.

## 📚 Table of Contents
- [✨ Features](#-features)
- [🛠️ Getting Started: Setup & Run](#️-getting-started-setup--run)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [🔧 API Integration Guide](#-api-integration-guide)
  - [Endpoints](#endpoints)
  - [Example Usage](#example-usage)
- [🖼️ Image & Comic Generation](#️-image--comic-generation)
- [🤖 Swarm Intelligence](#-swarm-intelligence)
- [💻 Frontend Guide](#-frontend-guide)
  - [Getting Started with Next.js](#getting-started-with-nextjs)
  - [Learn More](#learn-more)
- [🚀 Deploy on Vercel](#-deploy-on-vercel)
- [🤔 Troubleshooting](#-troubleshooting)
  - [Swagger UI Fix](#swagger-ui-fix)
- [💡 GitHub Copilot Prompts](#-github-copilot-prompts)

---

## ✨ Features

*   **Dynamic Story Generation**: Creates unique stories from user prompts using generative AI.
*   **Image Generation**: Produces accompanying images to visualize the story.
*   **Comic Strip Creation**: Generates comic book-style panels for a richer narrative experience.
*   **FastAPI Backend**: A robust and scalable backend built with Python.
*   **Next.js Frontend**: A modern, reactive, and user-friendly interface built with TypeScript and React.
*   **Swarm Intelligence**: Utilizes a multi-agent system for handling complex generation tasks.

---

## 🛠️ Getting Started: Setup & Run

Follow these steps to get the development environment up and running on your local machine.

### Prerequisites

*   Python 3.11+
*   Node.js 18.17+
*   An active Google AI Studio API Key.

### Backend Setup

1.  **Navigate to the backend directory and create a virtual environment**:
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate
    ```
2.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure Environment Variables**:
    - Create a `.env` file inside the `backend` directory.
    - Add your Google AI API key to the file:
      ```
      GOOGLE_API_KEY="your_super_secret_api_key"
      ```
4.  **Run the Backend Server**:
    ```bash
    uvicorn enhanced_backend:app --reload
    ```
    The backend will be accessible at `http://localhost:8000`.

### Frontend Setup

1.  **Navigate to the UI directory**:
    ```bash
    cd new_ui
    ```
2.  **Install Node.js dependencies**:
    ```bash
    npm install
    ```
3.  **Run the Frontend Development Server**:
    ```bash
    npm run dev
    ```
    The frontend will be accessible at `http://localhost:3000`.

---

## 🔧 API Integration Guide

The FastAPI backend provides a simple yet powerful API.

### Endpoints

- **`GET /`**: A welcome endpoint to confirm the server is running.
- **`POST /generate_story`**: The core endpoint for generating a story from a prompt.
  - **Request Body**: `{"prompt": "A tale of a mischievous dragon..."}`
  - **Returns**: `{"story": "The generated story text..."}`
- **`POST /generate_story_with_images`**: Generates a story and a set of images.
- **`POST /generate_story_with_comic`**: Generates a story and a comic strip.
- **`GET /docs`**: Access the interactive Swagger UI documentation.
- **`GET /redoc`**: Access the ReDoc documentation.

### Example Usage

Here’s how to generate a story using `curl`:
```bash
curl -X POST "http://localhost:8000/generate_story" \
-H "Content-Type: application/json" \
-d '{"prompt": "A story about a brave knight defending a castle."}'
```

---

## 🖼️ Image & Comic Generation

The `gemini_image_generator.py` script uses the Gemini Pro Vision model to create images based on text prompts.

- **Key Function**: `generate_image(prompt)`
- **Output**: Images are saved to the `story_images` directory.

The comic generation follows a similar process, creating a sequence of images that form a narrative.

---

## 🤖 Swarm Intelligence

Our Swarm Intelligence implementation uses a multi-agent system to break down and solve complex generation tasks.

- **Core Components**:
  - `Agent`: An individual worker responsible for a specific task.
  - `Objective`: The high-level goal for the swarm.
  - `Swarm`: The orchestrator that manages the agents and their workflow.
- **How it Works**: An objective is defined, and the swarm coordinates multiple agents to collaboratively achieve it.

---

## 💻 Frontend Guide

The frontend is a [Next.js](https://nextjs.org/) application.

### Getting Started with Next.js

The main page can be found at `src/app/page.tsx`. You can edit this file to see live updates in your browser. This project uses [`next/font`](https://nextjs.org/docs/basic-features/font-optimization) to automatically optimize and load the Inter font.

### Learn More

- **Next.js Documentation**: [https://nextjs.org/docs](https://nextjs.org/docs)
- **Learn Next.js**: [https://nextjs.org/learn](https://nextjs.org/learn)

---

## 🚀 Deploy on Vercel

The easiest way to deploy this Next.js app is with the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme).

For more details, see the [Next.js deployment documentation](https://nextjs.org/docs/deployment).

---

## 🤔 Troubleshooting

### Swagger UI Fix

- **Problem**: The Swagger UI at `/docs` fails to load CSS or JavaScript assets.
- **Solution**: Ensure the `StaticFiles` middleware is correctly mounted in your FastAPI application and that the paths to static assets are correct.

---

## 💡 GitHub Copilot Prompts

Here are some useful prompts for developing with GitHub Copilot:

- `"How do I add a new component to the UI?"`
- `"What is the best way to manage state in the application?"`
- `"How do I deploy the Next.js application?"`