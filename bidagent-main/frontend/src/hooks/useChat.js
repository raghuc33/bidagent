import { useState, useEffect, useCallback } from 'react'
import { sendChatMessage, getChatHistory } from '../services/api'

export default function useChat(sessionId, sectionTitle, sectionDescription, docId) {
    const [messages, setMessages] = useState([])
    const [isLoading, setIsLoading] = useState(false)

    useEffect(() => {
        if (!sessionId) return
        getChatHistory(sessionId, '_global')
            .then(data => setMessages(data.messages || []))
            .catch(() => {})
    }, [sessionId])

    const sendMessage = useCallback(async (text, currentDraft) => {
        const userMsg = { role: 'user', content: text, tool_calls: [] }
        setMessages(prev => [...prev, userMsg])
        setIsLoading(true)

        try {
            const data = await sendChatMessage(
                sessionId, '_global', text, currentDraft,
                sectionTitle, sectionDescription, docId,
            )
            const resp = data.response
            const assistantMsg = {
                role: 'assistant',
                content: resp.text,
                tool_calls: resp.tool_calls || [],
                updated_draft: resp.updated_draft,
            }
            setMessages(prev => [...prev, assistantMsg])
            return resp
        } catch (err) {
            const errorMsg = { role: 'assistant', content: `Error: ${err.message}`, tool_calls: [] }
            setMessages(prev => [...prev, errorMsg])
            return null
        } finally {
            setIsLoading(false)
        }
    }, [sessionId, sectionTitle, sectionDescription, docId])

    return { messages, sendMessage, isLoading }
}
