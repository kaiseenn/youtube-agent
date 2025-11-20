import { useState, useRef, useEffect } from 'react'

function App() {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'auto' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage = inputValue.trim()
    setInputValue('')
    setIsLoading(true)

    setMessages(prev => [...prev, { role: 'user', content: userMessage }])

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let aiResponse = ''

      setMessages(prev => [...prev, { role: 'ai', content: '' }])

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        aiResponse += chunk

        setMessages(prev => {
          const newMessages = [...prev]
          newMessages[newMessages.length - 1] = {
            role: 'ai',
            content: aiResponse
          }
          return newMessages
        })
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', content: `Error: ${error.message}` }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="app-container">
      <div className="chat-wrapper">
        <header className="chat-header">
          <h1>YouTube Agent</h1>
        </header>
        
        <div className="messages-list">
          {messages.length === 0 && (
            <div className="empty-state">
              Ask something to get started...
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <div key={idx} className={`message-item ${msg.role}`}>
              <div className="message-sender">
                {msg.role === 'user' ? 'You' : 'Assistant'}
              </div>
              <div className="message-text">
                {msg.content}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message..."
            disabled={isLoading}
            autoFocus
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !inputValue.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

export default App
