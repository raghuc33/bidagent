import { useState, useEffect, useCallback } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useParams } from 'react-router-dom'
import { extractSections, generateBidResponse, getStoredUser, logout, createSession, getSession, updateSessionDrafts, listSessions } from '../services/api'
import useChat from '../hooks/useChat'
import usePipeline from '../hooks/usePipeline'
import ChatPanel from '../components/ChatPanel'
import PipelineProgress from '../components/PipelineProgress'
import SelectionToolbar from '../components/SelectionToolbar'
import LoadingSpinner from '../components/LoadingSpinner'
import ComplianceMatrix from '../components/ComplianceMatrix'
import ReactMarkdown from 'react-markdown'

const WORD_LIMIT = 250

function wordCount(text) {
    return text.trim() ? text.trim().split(/\s+/).length : 0
}

function BidBuilder() {
    const location = useLocation()
    const navigate = useNavigate()
    const params = useParams()
    const user = getStoredUser()

    // Can arrive via: (1) location.state from Home (new bid) or (2) URL param (resume)
    const locationState = location.state || {}
    const resumeSessionId = params.sessionId

    const [dbSessionId, setDbSessionId] = useState(null)
    const [tenderName, setTenderName] = useState(locationState.tenderName || '')
    const [tenderDocId, setTenderDocId] = useState(locationState.tenderDocId || '')
    const [sections, setSections] = useState([])
    const [responses, setResponses] = useState({})
    const [activeSection, setActiveSection] = useState(null)
    const [loading, setLoading] = useState(true)
    const [extractError, setExtractError] = useState(null)
    const [chatWidth, setChatWidth] = useState(30)
    const [isDragging, setIsDragging] = useState(false)
    const [generatingAll, setGeneratingAll] = useState(false)
    const [generatingSection, setGeneratingSection] = useState(null)
    const [showCompliance, setShowCompliance] = useState(false)
    const [existingSession, setExistingSession] = useState(null) // prompt user if duplicate found
    const [selectedText, setSelectedText] = useState('')
    const [selectionPos, setSelectionPos] = useState(null)
    const [chatContext, setChatContext] = useState('')
    const [saveStatus, setSaveStatus] = useState('')

    const sessionId = tenderDocId || 'default'
    const activeData = activeSection ? sections.find(s => s.id === activeSection) : null

    const { phases, isRunning, result: pipelineResult, runPipeline } = usePipeline()

    const chat = useChat(
        sessionId,
        activeData?.title || '',
        activeData?.description || '',
        tenderDocId,
    )

    useEffect(() => {
        if (resumeSessionId) {
            loadSavedSession(resumeSessionId)
        } else if (locationState.tenderDocId) {
            loadNewSession()
        } else {
            navigate('/')
        }
    }, [])

    useEffect(() => {
        if (!pipelineResult || !activeSection) return
        if (pipelineResult.error) return

        setResponses(prev => ({
            ...prev,
            [activeSection]: {
                text: pipelineResult.final_draft || '',
                sources: pipelineResult.sources || [],
                score: pipelineResult.score,
                wordCount: pipelineResult.word_count || 0,
            }
        }))
    }, [pipelineResult])

    // Autosave drafts (debounced 3 seconds after last change)
    useEffect(() => {
        if (!dbSessionId || Object.keys(responses).length === 0) return
        const timer = setTimeout(async () => {
            try {
                await updateSessionDrafts(dbSessionId, responses)
                setSaveStatus('Saved')
                setTimeout(() => setSaveStatus(''), 2000)
            } catch {
                setSaveStatus('Save failed')
            }
        }, 3000)
        return () => clearTimeout(timer)
    }, [responses, dbSessionId])

    // Load a saved session (resume)
    const loadSavedSession = async (sid) => {
        try {
            const data = await getSession(sid)
            const s = data.session
            setDbSessionId(s.id)
            setTenderName(s.tender_name)
            setTenderDocId(s.tender_doc_id || '')
            setSections(s.sections || [])
            setResponses(s.drafts || {})
            if (s.sections?.length > 0) setActiveSection(s.sections[0].id)
        } catch (err) {
            setExtractError(err.message)
        } finally {
            setLoading(false)
        }
    }

    // Start a new session (from upload) — checks for existing first
    const loadNewSession = async () => {
        try {
            // Check if a session with this tender already exists
            const sessionsData = await listSessions()
            const existing = (sessionsData.sessions || []).find(
                s => s.tender_doc_id === locationState.tenderDocId
            )

            if (existing) {
                setExistingSession(existing)
                setLoading(false)
                return
            }

            await createAndGenerate()
        } catch (err) {
            setExtractError(err.message)
            setLoading(false)
        }
    }

    const handleUseExisting = () => {
        const s = existingSession
        setExistingSession(null)
        setDbSessionId(s.id)
        setTenderName(s.tender_name)
        setTenderDocId(s.tender_doc_id || '')
        setSections(s.sections || [])
        setResponses(s.drafts || {})
        if (s.sections?.length > 0) setActiveSection(s.sections[0].id)
    }

    const handleCreateNew = async () => {
        setExistingSession(null)
        setLoading(true)
        try {
            await createAndGenerate()
        } catch (err) {
            setExtractError(err.message)
            setLoading(false)
        }
    }

    const createAndGenerate = async () => {
        const data = await extractSections(locationState.tenderName, locationState.tenderDocId)
        setSections(data.sections)
        if (data.sections.length > 0) setActiveSection(data.sections[0].id)

        const sessionData = await createSession(
            locationState.tenderName || 'Untitled Tender',
            locationState.tenderDocId,
            data.sections,
            {},
        )
        setDbSessionId(sessionData.session.id)
        setLoading(false)

        if (data.sections.length > 0) {
            generateAllSections(data.sections)
        }
    }

    const generateAllSections = async (sectionsList) => {
        setGeneratingAll(true)
        for (const section of sectionsList) {
            setGeneratingSection(section.id)
            setActiveSection(section.id)
            try {
                const data = await generateBidResponse(section.title, section.description, tenderDocId)
                setResponses(prev => ({
                    ...prev,
                    [section.id]: {
                        text: data.text,
                        sources: data.sources || [],
                        score: null,
                        wordCount: data.word_count,
                    }
                }))
            } catch (err) {
                setResponses(prev => ({
                    ...prev,
                    [section.id]: { text: '', sources: [], score: null, wordCount: 0, error: err.message }
                }))
            }
        }
        setGeneratingSection(null)
        setGeneratingAll(false)
    }

    const handleGenerate = (section) => {
        setActiveSection(section.id)
        runPipeline(section.title, section.description, tenderDocId, sessionId, section.id)
    }

    const handleTextChange = (sectionId, newText) => {
        setResponses(prev => ({
            ...prev,
            [sectionId]: { ...prev[sectionId], text: newText, wordCount: wordCount(newText) }
        }))
    }

    const handleChatSend = async (text) => {
        const currentDraft = responses[activeSection]?.text || ''
        const resp = await chat.sendMessage(text, currentDraft)
        if (resp?.updated_draft && activeSection) {
            setResponses(prev => ({
                ...prev,
                [activeSection]: {
                    ...prev[activeSection],
                    text: resp.updated_draft,
                    wordCount: wordCount(resp.updated_draft),
                }
            }))
        }
    }

    const handleExport = () => {
        let output = `# ${tenderName || 'Bid Response'}\n\n`
        sections.forEach(s => {
            const r = responses[s.id]
            output += `## ${s.title}\n\n`
            output += r?.text ? `${r.text}\n\n` : `[Not completed]\n\n`
            if (r?.score) output += `Score: ${r.score}/100\n`
            output += `Words: ${r?.wordCount || 0}/${s.word_limit || WORD_LIMIT}\n\n---\n\n`
        })
        const blob = new Blob([output], { type: 'text/markdown' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${(tenderName || 'bid').replace(/\s+/g, '-').toLowerCase()}.md`
        a.click()
        URL.revokeObjectURL(url)
    }

    const handleLogout = () => { logout(); navigate('/login') }

    const handleResizeStart = (e) => {
        e.preventDefault()
        setIsDragging(true)
        const startX = e.clientX
        const startWidth = chatWidth
        const onMouseMove = (e) => {
            const delta = e.clientX - startX
            const newPct = Math.min(55, Math.max(15, startWidth + (delta / document.body.clientWidth) * 100))
            setChatWidth(newPct)
        }
        const onMouseUp = () => {
            setIsDragging(false)
            document.removeEventListener('mousemove', onMouseMove)
            document.removeEventListener('mouseup', onMouseUp)
        }
        document.addEventListener('mousemove', onMouseMove)
        document.addEventListener('mouseup', onMouseUp)
    }

    // Text selection — works for both textareas and regular text
    const handleTextSelect = useCallback((e) => {
        setTimeout(() => {
            const el = e.target

            // Handle textarea selection
            if (el.tagName === 'TEXTAREA' && el.selectionStart !== el.selectionEnd) {
                const text = el.value.substring(el.selectionStart, el.selectionEnd).trim()
                if (text.length > 2) {
                    const rect = el.getBoundingClientRect()
                    setSelectedText(text)
                    setSelectionPos({ top: rect.top, left: rect.left + rect.width / 2 - 60 })
                    return
                }
            }

            // Handle regular text selection
            const sel = window.getSelection()
            const text = sel?.toString().trim()
            if (text && text.length > 2 && sel.rangeCount > 0) {
                const range = sel.getRangeAt(0)
                const rect = range.getBoundingClientRect()
                setSelectedText(text)
                setSelectionPos({ top: rect.top, left: rect.left + rect.width / 2 - 60 })
                return
            }

            setSelectedText('')
            setSelectionPos(null)
        }, 10)
    }, [])

    // Clear toolbar when clicking without selecting
    useEffect(() => {
        const handleClick = (e) => {
            // Don't clear if clicking the toolbar itself
            if (e.target.closest('[data-selection-toolbar]')) return
            if (!window.getSelection()?.toString().trim()) {
                setSelectedText('')
                setSelectionPos(null)
            }
        }
        document.addEventListener('mousedown', handleClick)
        return () => document.removeEventListener('mousedown', handleClick)
    }, [])

    const handleAddToChat = () => {
        setChatContext(selectedText)
        setSelectedText('')
        setSelectionPos(null)
    }

    const handleRewrite = () => {
        const text = selectedText
        setSelectedText('')
        setSelectionPos(null)
        handleChatSend(`Rewrite the following text, keeping the same meaning but improving clarity and quality:\n\n"${text}"`)
    }

    const handleImprove = () => {
        const text = selectedText
        setSelectedText('')
        setSelectionPos(null)
        handleChatSend(`Improve the following text — make it stronger, more specific, and more compelling:\n\n"${text}"`)
    }

    const completedCount = Object.values(responses).filter(r => r?.text).length

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen gap-4">
                <LoadingSpinner size="lg" />
                <p className="text-gray-500 text-sm">Analyzing tender document...</p>
            </div>
        )
    }

    if (extractError) {
        return (
            <div className="max-w-lg mx-auto mt-20 p-8 text-center">
                <h2 className="text-xl font-semibold text-red-600 mb-4">Failed to analyze tender</h2>
                <p className="text-gray-600 mb-6">{extractError}</p>
                <button onClick={() => navigate('/')} className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600">Go back</button>
            </div>
        )
    }

    if (existingSession) {
        return (
            <div className="max-w-lg mx-auto mt-20 p-8 text-center font-sans">
                <h2 className="text-xl font-semibold mb-2">Existing bid found</h2>
                <p className="text-gray-500 mb-2 text-sm">
                    You already have a bid session for <strong>{existingSession.tender_name}</strong>
                </p>
                <p className="text-gray-400 text-xs mb-8">
                    {existingSession.sections_completed}/{existingSession.sections_total} sections completed · Last edited {new Date(existingSession.updated_at).toLocaleDateString()}
                </p>
                <div className="flex gap-3 justify-center">
                    <button
                        onClick={handleUseExisting}
                        className="px-6 py-2.5 bg-blue-500 text-white rounded-md font-medium hover:bg-blue-600"
                    >
                        Continue existing bid
                    </button>
                    <button
                        onClick={handleCreateNew}
                        className="px-6 py-2.5 bg-white text-gray-700 border border-gray-300 rounded-md font-medium hover:bg-gray-50"
                    >
                        Start fresh
                    </button>
                </div>
                <button onClick={() => navigate('/')} className="mt-6 text-xs text-gray-400 hover:text-gray-600 underline">
                    Back to dashboard
                </button>
            </div>
        )
    }

    return (
        <div className="h-screen flex flex-col font-sans bg-gray-50">
            {/* Top bar */}
            <div className="flex justify-between items-center px-6 py-2 border-b border-gray-200 bg-white shrink-0">
                <div className="flex items-center gap-4">
                    <button onClick={() => navigate('/')} className="px-2.5 py-1 bg-gray-100 text-gray-600 hover:bg-gray-200 rounded text-xs font-medium">Dashboard</button>
                    <div>
                        <h1 className="text-base font-bold">{tenderName || 'Bid Builder'}</h1>
                        <p className="text-[11px] text-gray-400">
                            {completedCount}/{sections.length} sections
                            {saveStatus && <span className="ml-2 text-green-500">{saveStatus}</span>}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <button onClick={() => setShowCompliance(true)} className="px-3 py-1.5 bg-green-600 text-white rounded text-xs font-medium hover:bg-green-700">
                        Compliance
                    </button>
                    <button onClick={handleExport} className="px-3 py-1.5 bg-blue-500 text-white rounded text-xs font-medium hover:bg-blue-600">
                        Export
                    </button>
                    <span className="text-xs text-gray-400">{user?.name}</span>
                    <button onClick={handleLogout} className="text-xs text-gray-400 hover:text-gray-600">Sign out</button>
                </div>
            </div>

            {/* Pipeline stages */}
            <div className="flex items-center gap-0.5 px-3 py-2 bg-white border-b border-gray-200 overflow-x-auto shrink-0">
                {sections.map((section, i) => {
                    const r = responses[section.id]
                    const isActive = activeSection === section.id
                    const isDone = !!r?.text
                    const isGenerating = (isActive && isRunning) || generatingSection === section.id

                    return (
                        <div key={section.id} className="flex items-center shrink-0">
                            {i > 0 && <div className="w-3 h-px bg-gray-300" />}
                            <button
                                onClick={() => setActiveSection(section.id)}
                                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[11px] font-medium transition-all whitespace-nowrap ${
                                    isActive ? 'bg-blue-500 text-white'
                                    : isDone ? 'bg-green-50 text-green-700 hover:bg-green-100'
                                    : 'text-gray-500 hover:bg-gray-100'
                                }`}
                            >
                                <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold shrink-0 ${
                                    isActive ? 'bg-white/25' : isDone ? 'bg-green-500 text-white' : 'bg-gray-200'
                                }`}>
                                    {isGenerating ? '~' : isDone ? '✓' : i + 1}
                                </span>
                                <span className="max-w-[100px] truncate">{section.title}</span>
                                {r?.score && <span className={`text-[9px] ${isActive ? 'opacity-75' : 'text-blue-600'}`}>{r.score}</span>}
                            </button>
                        </div>
                    )
                })}
            </div>

            {/* Main: Chat + Resize + Document */}
            <div className={`flex flex-1 overflow-hidden ${isDragging ? 'select-none cursor-col-resize' : ''}`}>
                {/* Chat */}
                <div style={{ width: `${chatWidth}%` }} className="shrink-0 border-r border-gray-200 bg-white">
                    <ChatPanel
                        messages={chat.messages}
                        onSend={handleChatSend}
                        isLoading={chat.isLoading}
                        sectionTitle={tenderName || 'Bid Assistant'}
                        contextText={chatContext}
                        onClearContext={() => setChatContext('')}
                    />
                </div>

                {/* Resize handle */}
                <div
                    onMouseDown={handleResizeStart}
                    className={`w-1 cursor-col-resize shrink-0 ${isDragging ? 'bg-blue-400' : 'hover:bg-blue-300'}`}
                />

                {/* Document */}
                <div className="flex-1 overflow-y-auto min-w-0 relative" onMouseUp={handleTextSelect}>
                    {/* Selection toolbar */}
                    <SelectionToolbar
                        position={selectionPos}
                        onAddToChat={handleAddToChat}
                        onRegenerate={handleRewrite}
                        onImprove={handleImprove}
                    />
                    <div className="px-10 py-8">
                        {/* Document header */}
                        <div className="mb-8">
                            <h2 className="text-2xl font-bold text-gray-900">{tenderName || 'Bid Response'}</h2>
                            <div className="h-px bg-gray-200 mt-4" />
                        </div>

                        {/* Sections as a flowing document */}
                        {sections.map((section) => {
                            const r = responses[section.id]
                            const isActive = activeSection === section.id
                            const wc = r?.wordCount || 0
                            const limit = section.word_limit || WORD_LIMIT
                            const over = wc > limit

                            return (
                                <div
                                    key={section.id}
                                    className={`mb-2 cursor-pointer transition-all ${isActive ? '' : ''}`}
                                    onClick={() => setActiveSection(section.id)}
                                >
                                    {/* Section heading */}
                                    <div className="flex items-baseline justify-between mb-2">
                                        <h3 className={`text-base font-semibold ${isActive ? 'text-blue-600' : 'text-gray-800'}`}>
                                            {section.title}
                                        </h3>
                                        <div className="flex items-center gap-2 shrink-0 ml-4">
                                            {r?.score && (
                                                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                                    r.score >= 70 ? 'bg-green-100 text-green-700'
                                                    : r.score >= 50 ? 'bg-yellow-100 text-yellow-700'
                                                    : 'bg-red-100 text-red-600'
                                                }`}>{r.score}/100</span>
                                            )}
                                            <span className={`text-[10px] ${over ? 'text-red-500 font-medium' : 'text-gray-400'}`}>
                                                {wc}/{limit}w
                                            </span>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handleGenerate(section) }}
                                                disabled={(isActive && isRunning) || generatingAll}
                                                className="px-2 py-0.5 bg-blue-500 text-white text-[10px] rounded hover:bg-blue-600 disabled:opacity-50"
                                            >
                                                {r?.text ? 'Regen' : 'Generate'}
                                            </button>
                                        </div>
                                    </div>

                                    {section.description && (
                                        <p className="text-xs text-gray-400 mb-2 italic">{section.description}</p>
                                    )}

                                    {/* Pipeline progress */}
                                    {isActive && isRunning && (
                                        <div className="mb-3 p-3 bg-blue-50 rounded-lg">
                                            <PipelineProgress phases={phases} />
                                        </div>
                                    )}

                                    {isActive && pipelineResult?.error && (
                                        <div className="mb-3 p-2 bg-red-50 text-red-600 text-xs rounded">{pipelineResult.error}</div>
                                    )}

                                    {/* Content */}
                                    {r?.text ? (
                                        <div className="mb-1">
                                            {isActive ? (
                                                <textarea
                                                    value={r.text}
                                                    onChange={(e) => handleTextChange(section.id, e.target.value)}
                                                    className="w-full p-2 text-sm leading-relaxed text-gray-700 bg-white border border-blue-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-300 resize-y"
                                                    rows={Math.max(6, Math.ceil(r.text.length / 80))}
                                                />
                                            ) : (
                                                <div
                                                    className="prose prose-sm max-w-none text-gray-700 cursor-pointer"
                                                    onClick={() => setActiveSection(section.id)}
                                                >
                                                    <ReactMarkdown>{r.text}</ReactMarkdown>
                                                </div>
                                            )}
                                            {r.sources?.length > 0 && isActive && (
                                                <div className="flex flex-wrap gap-1 mt-1">
                                                    {r.sources.map((s, i) => (
                                                        <span key={i} className="text-[9px] bg-gray-100 text-gray-400 px-1 py-0.5 rounded">
                                                            {s.filename} p.{s.page}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    ) : generatingSection === section.id ? (
                                        <div className="flex items-center gap-2 py-4 text-sm text-blue-500">
                                            <LoadingSpinner size="sm" />
                                            <span>Generating...</span>
                                        </div>
                                    ) : (
                                        <p className="text-sm text-gray-300 italic mb-1">
                                            {generatingAll ? 'Waiting...' : 'Click Generate to create this section'}
                                        </p>
                                    )}

                                    {/* Divider between sections */}
                                    <div className="h-px bg-gray-100 my-5" />
                                </div>
                            )
                        })}
                    </div>
                </div>
            </div>

            {/* Compliance Matrix Modal */}
            {showCompliance && (
                <ComplianceMatrix
                    drafts={sections.map(s => {
                        const r = responses[s.id]
                        return r?.text ? `## ${s.title}\n${r.text}` : ''
                    }).filter(Boolean).join('\n\n')}
                    onClose={() => setShowCompliance(false)}
                />
            )}
        </div>
    )
}

export default BidBuilder
