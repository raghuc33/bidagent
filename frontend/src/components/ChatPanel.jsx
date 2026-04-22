import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

const SUGGESTIONS = [
    'Make it more concise',
    'Strengthen the evidence',
    'Improve the score',
]

function ChatPanel({ messages, onSend, isLoading, sectionTitle, contextText, onClearContext }) {
    const [input, setInput] = useState('')
    const bottomRef = useRef(null)
    const inputRef = useRef(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, isLoading])

    useEffect(() => {
        inputRef.current?.focus()
    }, [messages, isLoading, sectionTitle, contextText])

    const handleSend = () => {
        const text = input.trim()
        if (!text || isLoading) return

        // Prepend context if present
        const fullMessage = contextText
            ? `Regarding this text: "${contextText}"\n\n${text}`
            : text

        setInput('')
        if (onClearContext) onClearContext()
        onSend(fullMessage)
        setTimeout(() => inputRef.current?.focus(), 0)
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <div className="flex flex-col h-full bg-white">
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
                <div className="text-sm font-medium text-gray-700">Chat</div>
                <div className="text-xs text-gray-400">{sectionTitle}</div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
                {messages.length === 0 && !isLoading && (
                    <div className="text-center text-sm text-gray-400 mt-8">
                        <p className="mb-4">Ask me to refine this section</p>
                        <div className="flex flex-wrap gap-2 justify-center">
                            {SUGGESTIONS.map(s => (
                                <button
                                    key={s}
                                    onClick={() => onSend(s)}
                                    className="text-xs bg-blue-50 text-blue-600 px-3 py-1.5 rounded-full hover:bg-blue-100"
                                >
                                    {s}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                            msg.role === 'user'
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-100 text-gray-800'
                        }`}>
                            {msg.tool_calls?.length > 0 && (
                                <div className="mb-2 space-y-1">
                                    {msg.tool_calls.map((tc, j) => (
                                        <div key={j} className="text-xs bg-blue-50 border border-blue-200 text-blue-700 rounded px-2 py-1">
                                            {tc.summary || tc.tool}
                                        </div>
                                    ))}
                                </div>
                            )}
                            {msg.role === 'assistant' ? (
                                <div className="prose prose-sm max-w-none prose-p:my-1 prose-li:my-0 prose-ul:my-1 prose-ol:my-1 prose-headings:my-2">
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                </div>
                            ) : (
                                <div className="whitespace-pre-wrap">{msg.content}</div>
                            )}
                            {msg.updated_draft && (
                                <div className="mt-2 text-xs text-green-600 bg-green-50 rounded px-2 py-1">
                                    Draft updated
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-gray-100 rounded-lg px-3 py-2 text-sm text-gray-400 animate-pulse">
                            Thinking...
                        </div>
                    </div>
                )}

                <div ref={bottomRef} />
            </div>

            {/* Context quote (selected text) */}
            {contextText && (
                <div className="px-4 pt-2">
                    <div className="flex items-start gap-2 bg-blue-50 border border-blue-200 rounded-md px-3 py-2">
                        <div className="flex-1 text-xs text-blue-700 line-clamp-3 border-l-2 border-blue-400 pl-2 italic">
                            "{contextText}"
                        </div>
                        <button
                            onClick={onClearContext}
                            className="text-blue-400 hover:text-blue-600 text-xs shrink-0 mt-0.5"
                        >
                            ✕
                        </button>
                    </div>
                </div>
            )}

            {/* Input */}
            <div className="px-4 py-3 border-t border-gray-200">
                <div className="flex gap-2">
                    <input
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={contextText ? 'What should I do with this text?' : 'Refine this section...'}
                        disabled={isLoading}
                        autoFocus
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                    />
                    <button
                        onClick={handleSend}
                        disabled={!input.trim() || isLoading}
                        className="px-4 py-2 bg-blue-500 text-white rounded-md text-sm hover:bg-blue-600 disabled:opacity-50"
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    )
}

export default ChatPanel
