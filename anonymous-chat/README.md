# 🎭 Anonymous Chat Application

A modern, real-time anonymous chat application with voting functionality built with React and Node.js.

## ✨ Features

- **Anonymous Messaging**: Auto-generated anonymous usernames for complete privacy
- **Real-time Communication**: Instant messaging using Socket.io
- **Message Voting**: Upvote and downvote messages to show engagement
- **User Count**: See how many people are currently online
- **Modern UI**: Beautiful glassmorphism design with smooth animations
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Auto-scroll**: Automatic scrolling to latest messages
- **Message Limits**: 500 character limit per message
- **Message History**: Last 100 messages are stored and displayed

## 🚀 Quick Start

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd anonymous-chat
   ```

2. **Install backend dependencies:**
   ```bash
   cd backend
   npm install
   ```

3. **Install frontend dependencies:**
   ```bash
   cd ../frontend
   npm install
   ```

### Running the Application

1. **Start the backend server:**
   ```bash
   cd backend
   npm start
   ```
   The server will run on `http://localhost:5000`

2. **Start the frontend development server:**
   ```bash
   cd frontend
   npm start
   ```
   The application will open in your browser at `http://localhost:3000`

### Development Mode

For development with auto-restart:

**Backend (with nodemon):**
```bash
cd backend
npm run dev
```

**Frontend:**
```bash
cd frontend
npm start
```

## 🏗️ Architecture

### Backend (Node.js + Express + Socket.io)
- Express server for API endpoints
- Socket.io for real-time messaging
- In-memory storage for messages and users
- Anonymous username generation
- Message voting system

### Frontend (React + Socket.io Client)
- Modern React with hooks
- Real-time updates via Socket.io
- Responsive design with CSS Grid/Flexbox
- Smooth animations and transitions

## 📁 Project Structure

```
anonymous-chat/
├── backend/
│   ├── package.json
│   └── server.js
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   └── manifest.json
│   ├── src/
│   │   ├── App.js
│   │   ├── App.css
│   │   ├── index.js
│   │   └── index.css
│   └── package.json
└── README.md
```

## 🎮 Usage

1. **Join the Chat**: Open the application in your browser
2. **Anonymous Identity**: You'll automatically get an anonymous username
3. **Send Messages**: Type in the input field and press Send or Enter
4. **Vote on Messages**: Use 👍 and 👎 buttons to vote on messages
5. **See Activity**: Monitor online user count and message voting scores

## 🔧 Configuration

### Backend Configuration

The server runs on port 5000 by default. You can change this by setting the `PORT` environment variable:

```bash
PORT=8000 npm start
```

### Frontend Configuration

The frontend expects the backend to run on `http://localhost:5000`. If you change the backend port, update the socket connection in `src/App.js`:

```javascript
const socket = io('http://localhost:YOUR_PORT');
```

## 🚀 Deployment

### Backend Deployment

1. Set up your production environment
2. Set the `PORT` environment variable
3. Run `npm start`

### Frontend Deployment

1. Build the production version:
   ```bash
   npm run build
   ```
2. Serve the `build` folder using a static file server

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📝 License

This project is open source and available under the MIT License.

## 🎨 Features in Detail

### Anonymous Usernames
- Auto-generated creative names like "MysteriousWanderer123"
- No registration or personal information required
- New username assigned for each session

### Real-time Messaging
- Instant message delivery using WebSocket connections
- Auto-scroll to latest messages
- Connection status indicators

### Voting System
- One vote per user per message
- Visual feedback with color-coded vote counts
- Real-time vote updates across all connected users

### Modern UI/UX
- Glassmorphism design with backdrop blur effects
- Smooth animations and transitions
- Responsive design for all screen sizes
- Dark theme optimized for readability

## 🔮 Future Enhancements

- Private rooms/channels
- Message reactions (emoji)
- User profiles (optional)
- Message search and filtering
- Export chat history
- Admin moderation tools
- Custom themes
- File/image sharing

---

Built with ❤️ using React and Node.js