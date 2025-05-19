# Real-Time Translation Network

## Overview
This project is a real-time translation network that utilizes various services for language detection and translation. This README provides a step-by-step guide to set up and run the application.

## Architectural Diagram

Below is the architectural diagram depicting the components involved in the project:

https://drive.google.com/file/d/1t65usTmjxZzilIybmQqKXp1txFfSZ9Po/view

+----------------------- High-Level Architecture Diagram -----------------------+

+-------------------+
|      Frontend     |
| (HTML, CSS, JS)   |
+---------+---------+
          |
          | API Calls
          |
+---------v---------+
|      App Service  |
| (FastAPI)         |
+---------+---------+
          |
          | Interacts with
          |
+---------v---------+                       +---------------------+
| Language Detection |<-------------------->|   RabbitMQ          |
| Service (FastAPI)  |                      | (Message Broker)    |
+---------+---------+   Detects Language    +---------------------+
          |
          | 
          |
+---------v---------+                      +---------------------+
| Translation       |<-------------------->|   RabbitMQ          |
| Service (FastAPI) |       Performs       | (Message Broker)    |
+---------+---------+     Translations     +---------------------+

+------------------------------------------------------------------------------+

## Prerequisites

1. **Docker**: Ensure you have Docker installed on your machine.
   - **Ubuntu**: You can install Docker by following the official [Docker installation guide for Ubuntu](https://docs.docker.com/engine/install/ubuntu/).
   - **Windows**: Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop).

2. **Python**: Make sure you have Python 3.7 or higher installed. You can download it from the official [Python website](https://www.python.org/downloads/).

3. **Pip**: Ensure you have `pip` installed to manage Python packages.

4. **VSCode** (optional): For a better development experience, you can use Visual Studio Code with the appropriate extensions.

## Setting Up RabbitMQ

### Using Docker

1. **Pull the RabbitMQ Docker Image**:
   Open your terminal and run the following command:
   ```bash
   docker pull rabbitmq:management
   ```

2. **Run the RabbitMQ Container**:
   After pulling the image, run the RabbitMQ server with the following command:
   ```bash
   docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
   ```
   - The RabbitMQ management interface will be accessible at `http://localhost:15672` (default username: `guest`, password: `guest`).

## Serving the Frontend

You can serve the static files (HTML, CSS, JS) in the frontend folder using either of the following methods:

1. **Using VSCode Server Extension**:
   - Open the frontend folder in VSCode.
   - Use the Live Server extension to serve the files.

2. **Using Python's HTTP Server**:
   - Navigate to the frontend directory in your terminal:
   ```bash
   cd path/to/frontend
   ```
   - Run the following command:
   ```bash
   python -m http.server
   ```
   - The frontend will be accessible at `http://localhost:8000`.

## Running the Backend Services

The backend consists of three services: app, language detection, and translation. You need to run each service separately.

1. **Run the App Service**:
   - Navigate to the app directory:
   ```bash
   cd backend/app
   ```
   - Start the service with:
   ```bash
   python main.py
   ```

2. **Run the Language Detection Service**:
   - Navigate to the language detection directory:
   ```bash
   cd backend/language_detection
   ```
   - Start the service with:
   ```bash
   python main.py
   ```

3. **Run the Translation Service**:
   - Navigate to the translation directory:
   ```bash
   cd backend/translation
   ```
   - Start the service with:
   ```bash
   python main.py
   ```
   - You will need to create a environment variable for the openai api you can either create a .env file or store the OPENAI_API_KEY in machine's environment.
   ```python
   OPENAI_API_KEY='your_key'
   ```

## Conclusion

After following these steps, your application should be up and running. You can access the frontend and interact with the language detection and translation services. If you encounter any issues, please refer to the logs in your terminal for debugging information.

Happy coding!
#
