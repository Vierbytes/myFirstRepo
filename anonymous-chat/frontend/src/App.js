import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import './App.css';

const socket = io('http://localhost:5000');

function App() {
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [username, setUsername] = useState('');
  const [userCount, setUserCount] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    // Socket connection events
    socket.on('connect', () => {
      setIsConnected(true);
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
    });

    socket.on('username_assigned', (assignedUsername) => {
      setUsername(assignedUsername);
    });

    socket.on('initial_messages', (initialMessages) => {
      setMessages(initialMessages);
    });

    socket.on('new_message', (message) => {
      setMessages(prev => [...prev, message]);
    });

    socket.on('message_updated', (update) => {
      setMessages(prev => 
        prev.map(msg => 
          msg.id === update.messageId 
            ? { ...msg, votes: update.votes, voters: update.voters }
            : msg
        )
      );
    });

    socket.on('user_count', (count) => {
      setUserCount(count);
    });

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('username_assigned');
      socket.off('initial_messages');
      socket.off('new_message');
      socket.off('message_updated');
      socket.off('user_count');
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = (e) => {
    e.preventDefault();
    if (messageInput.trim() && isConnected) {
      socket.emit('send_message', { text: messageInput.trim() });
      setMessageInput('');
    }
  };

  const voteMessage = (messageId, voteType) => {
    socket.emit('vote_message', { messageId, voteType });
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getVoteColor = (votes) => {
    if (votes > 0) return '#10b981'; // green
    if (votes < 0) return '#ef4444'; // red
    return '#6b7280'; // gray
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>🎭 Anonymous Chat</h1>
          <div className="header-info">
            <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
              {isConnected ? '🟢' : '🔴'} {isConnected ? 'Connected' : 'Disconnected'}
            </span>
            <span className="user-count">👥 {userCount} online</span>
            {username && <span className="username">You: {username}</span>}
          </div>
        </div>
      </header>

      <main className="chat-container">
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-state">
              <h3>🌟 Welcome to Anonymous Chat!</h3>
              <p>Start a conversation and vote on messages you find interesting.</p>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className="message">
                <div className="message-header">
                  <span className="message-username">{message.username}</span>
                  <span className="message-time">{formatTime(message.timestamp)}</span>
                </div>
                <div className="message-content">
                  <p className="message-text">{message.text}</p>
                  <div className="message-actions">
                    <button 
                      className="vote-btn vote-up"
                      onClick={() => voteMessage(message.id, 'up')}
                      disabled={message.voters && message.voters.includes(socket.id)}
                    >
                      👍
                    </button>
                    <span 
                      className="vote-count"
                      style={{ color: getVoteColor(message.votes) }}
                    >
                      {message.votes}
                    </span>
                    <button 
                      className="vote-btn vote-down"
                      onClick={() => voteMessage(message.id, 'down')}
                      disabled={message.voters && message.voters.includes(socket.id)}
                    >
                      👎
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="message-form" onSubmit={sendMessage}>
          <div className="input-container">
            <input
              type="text"
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              placeholder="Type your anonymous message..."
              maxLength={500}
              disabled={!isConnected}
            />
            <button type="submit" disabled={!messageInput.trim() || !isConnected}>
              Send 📤
            </button>
          </div>
          <div className="input-info">
            <span>{messageInput.length}/500</span>
            {!isConnected && <span className="warning">Reconnecting...</span>}
          </div>
        </form>
      </main>
    </div>
  );
}

export default App;