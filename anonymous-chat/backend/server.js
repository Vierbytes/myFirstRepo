const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const { v4: uuidv4 } = require('uuid');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: true, // Allow all origins for mobile access
    methods: ["GET", "POST"],
    credentials: true
  }
});

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// In-memory storage (in production, you'd use a database)
let messages = [];
let users = new Map();

// Anonymous name generators
const adjectives = [
  'Mysterious', 'Anonymous', 'Silent', 'Shadow', 'Phantom', 'Ghost',
  'Whisper', 'Secret', 'Hidden', 'Masked', 'Cryptic', 'Enigma',
  'Stealth', 'Invisible', 'Unknown', 'Veiled', 'Cloaked', 'Nameless'
];

const nouns = [
  'User', 'Visitor', 'Wanderer', 'Stranger', 'Guest', 'Traveler',
  'Observer', 'Lurker', 'Watcher', 'Presence', 'Entity', 'Being',
  'Soul', 'Spirit', 'Figure', 'Person', 'Individual', 'Someone'
];

function generateAnonymousName() {
  const adj = adjectives[Math.floor(Math.random() * adjectives.length)];
  const noun = nouns[Math.floor(Math.random() * nouns.length)];
  const number = Math.floor(Math.random() * 999) + 1;
  return `${adj}${noun}${number}`;
}

// Socket.io connection handling
io.on('connection', (socket) => {
  console.log('User connected:', socket.id);
  
  // Generate anonymous username
  const username = generateAnonymousName();
  users.set(socket.id, { username, joinedAt: new Date() });
  
  // Send current messages to new user
  socket.emit('initial_messages', messages);
  socket.emit('username_assigned', username);
  
  // Broadcast user count
  io.emit('user_count', users.size);
  
  // Handle new message
  socket.on('send_message', (data) => {
    const user = users.get(socket.id);
    if (!user) return;
    
    const message = {
      id: uuidv4(),
      text: data.text,
      username: user.username,
      timestamp: new Date(),
      votes: 0,
      voters: new Set()
    };
    
    messages.push(message);
    
    // Keep only last 100 messages
    if (messages.length > 100) {
      messages = messages.slice(-100);
    }
    
    io.emit('new_message', {
      ...message,
      voters: Array.from(message.voters)
    });
  });
  
  // Handle message voting
  socket.on('vote_message', (data) => {
    const { messageId, voteType } = data;
    const message = messages.find(m => m.id === messageId);
    
    if (!message) return;
    
    const userId = socket.id;
    const hasVoted = message.voters.has(userId);
    
    if (voteType === 'up' && !hasVoted) {
      message.votes += 1;
      message.voters.add(userId);
    } else if (voteType === 'down' && !hasVoted) {
      message.votes -= 1;
      message.voters.add(userId);
    }
    
    io.emit('message_updated', {
      messageId: message.id,
      votes: message.votes,
      voters: Array.from(message.voters)
    });
  });
  
  // Handle disconnect
  socket.on('disconnect', () => {
    console.log('User disconnected:', socket.id);
    users.delete(socket.id);
    io.emit('user_count', users.size);
  });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'OK', users: users.size, messages: messages.length });
});

// Get messages endpoint
app.get('/api/messages', (req, res) => {
  const messagesWithArrayVoters = messages.map(msg => ({
    ...msg,
    voters: Array.from(msg.voters)
  }));
  res.json(messagesWithArrayVoters);
});

const PORT = process.env.PORT || 5000;
server.listen(PORT, '0.0.0.0', () => {
  console.log(`Anonymous chat server running on port ${PORT} and accessible from any device`);
});