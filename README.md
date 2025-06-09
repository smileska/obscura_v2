# Obscura Messenger

A real-time chat application built with Django Channels, featuring private messaging, group chatrooms, and real-time reactions.

## Features

- 🔐 User authentication and profiles  
- 💬 Private messaging
- 🏠 Group chatrooms with admin controls
- ⚡ Real-time messaging with WebSockets
- 😊 Message reactions
- 📷 Image sharing
- 🌙 Dark mode support
- 📱 Responsive design

## Architecture

- **Backend**: Django with Django Channels
- **Database**: PostgreSQL  
- **Cache/Message Broker**: Redis
- **Frontend**: Django Templates with Bootstrap 5
- **Containerization**: Docker & Docker Compose

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose

### Docker Development (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/obscura-messenger.git
   cd obscura-messenger