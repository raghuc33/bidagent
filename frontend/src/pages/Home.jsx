import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { logout, getStoredUser, uploadToKnowledgeBase, listSessions, deleteSession } from '../services/api'

function Home() {
    const navigate = useNavigate()
    const user = getStoredUser()
    const [tenderName, setTenderName] = useState('')
    const [tenderFile, setTenderFile] = useState(null)
    const [evidenceFiles, setEvidenceFiles] = useState([])
    const [uploading, setUploading] = useState(false)
    const [error, setError] = useState(null)
    const [uploadStatus, setUploadStatus] = useState('')
    const [sessions, setSessions] = useState([])
    const [loadingSessions, setLoadingSessions] = useState(true)
    const tenderRef = useRef(null)
    const evidenceRef = useRef(null)

    useEffect(() => {
        loadSessions()
    }, [])

    const loadSessions = async () => {
        try {
            const data = await listSessions()
            setSessions(data.sessions || [])
        } catch {} finally {
            setLoadingSessions(false)
        }
    }

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    const handleDelete = async (id, e) => {
        e.stopPropagation()
        if (!confirm('Delete this bid?')) return
        try {
            await deleteSession(id)
            setSessions(prev => prev.filter(s => s.id !== id))
        } catch {}
    }

    const handleStartBid = async () => {
        if (!tenderFile) {
            setError('Please upload a tender PDF')
            return
        }

        setError(null)
        setUploading(true)

        try {
            setUploadStatus('Uploading tender document...')
            const tenderResult = await uploadToKnowledgeBase(tenderFile)

            const evidenceDocIds = []
            for (let i = 0; i < evidenceFiles.length; i++) {
                setUploadStatus(`Uploading evidence ${i + 1} of ${evidenceFiles.length}...`)
                const result = await uploadToKnowledgeBase(evidenceFiles[i])
                evidenceDocIds.push(result.doc_id)
            }

            setUploadStatus('Processing complete. Opening Bid Builder...')

            navigate('/bid', {
                state: {
                    tenderName: tenderName || tenderFile.name.replace('.pdf', ''),
                    tenderDocId: tenderResult.doc_id,
                    evidenceDocIds,
                }
            })
        } catch (err) {
            setError(err.message)
        } finally {
            setUploading(false)
            setUploadStatus('')
        }
    }

    return (
        <div className="max-w-[900px] mx-auto px-8 py-12 font-sans">
            {/* Header */}
            <div className="flex justify-between items-center mb-10">
                <h1 className="text-2xl font-bold">BidAgent</h1>
                <div className="flex items-center gap-3">
                    <span className="text-sm text-gray-500">{user?.name || user?.email}</span>
                    <button onClick={handleLogout} className="text-sm text-gray-400 hover:text-gray-600 underline">
                        Sign out
                    </button>
                </div>
            </div>

            {/* Saved Sessions */}
            {!loadingSessions && sessions.length > 0 && (
                <div className="mb-8">
                    <h2 className="text-lg font-semibold mb-4">Continue Working</h2>
                    <div className="space-y-2">
                        {sessions.map(s => (
                            <div
                                key={s.id}
                                onClick={() => navigate(`/bid/${s.id}`)}
                                className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-5 py-4 cursor-pointer hover:border-blue-300 hover:shadow-sm transition-all"
                            >
                                <div>
                                    <div className="font-medium text-sm">{s.tender_name}</div>
                                    <div className="text-xs text-gray-400 mt-1">
                                        {s.sections_completed}/{s.sections_total} sections
                                        {' · '}
                                        {s.status === 'completed' ? 'Completed' : 'In progress'}
                                        {' · '}
                                        Last edited {new Date(s.updated_at).toLocaleDateString()}
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-blue-500 rounded-full"
                                            style={{ width: `${s.sections_total > 0 ? (s.sections_completed / s.sections_total) * 100 : 0}%` }}
                                        />
                                    </div>
                                    <button
                                        onClick={(e) => handleDelete(s.id, e)}
                                        className="text-gray-300 hover:text-red-500 text-xs"
                                    >
                                        Delete
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* New Bid Card */}
            <div className="bg-white border border-gray-200 rounded-xl p-8 mb-8">
                <h2 className="text-xl font-semibold mb-6">New Bid</h2>

                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tender Name</label>
                    <input
                        type="text"
                        value={tenderName}
                        onChange={(e) => setTenderName(e.target.value)}
                        placeholder="e.g. HMRC Debt Management"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                </div>

                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Statement of Requirements (SoR) *</label>
                    <div
                        onClick={() => tenderRef.current?.click()}
                        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all ${
                            tenderFile ? 'border-green-400 bg-green-50' : 'border-gray-300 bg-gray-50 hover:border-blue-400'
                        }`}
                    >
                        <input ref={tenderRef} type="file" accept=".pdf" onChange={(e) => setTenderFile(e.target.files[0])} className="hidden" />
                        {tenderFile ? (
                            <div className="text-green-700 font-medium">{tenderFile.name}</div>
                        ) : (
                            <>
                                <div className="text-3xl mb-2">📄</div>
                                <div className="text-gray-600">Upload tender PDF</div>
                            </>
                        )}
                    </div>
                </div>

                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Evidence / Case Studies (optional)</label>
                    <div
                        onClick={() => evidenceRef.current?.click()}
                        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all ${
                            evidenceFiles.length > 0 ? 'border-green-400 bg-green-50' : 'border-gray-300 bg-gray-50 hover:border-blue-400'
                        }`}
                    >
                        <input ref={evidenceRef} type="file" accept=".pdf" multiple onChange={(e) => setEvidenceFiles(Array.from(e.target.files))} className="hidden" />
                        {evidenceFiles.length > 0 ? (
                            <div className="text-green-700 font-medium">
                                {evidenceFiles.length} file{evidenceFiles.length > 1 ? 's' : ''} selected
                                <div className="text-sm text-green-600 mt-1">{evidenceFiles.map(f => f.name).join(', ')}</div>
                            </div>
                        ) : (
                            <>
                                <div className="text-3xl mb-2">📁</div>
                                <div className="text-gray-600">Upload case studies, past bids, evidence docs</div>
                            </>
                        )}
                    </div>
                </div>

                {error && <div className="bg-red-50 border border-red-200 rounded-md p-3 text-red-600 text-sm mb-4">{error}</div>}
                {uploadStatus && <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-blue-700 text-sm mb-4">{uploadStatus}</div>}

                <button
                    onClick={handleStartBid}
                    disabled={uploading || !tenderFile}
                    className="w-full py-3 bg-blue-500 text-white rounded-md font-semibold hover:bg-blue-600 disabled:opacity-50"
                >
                    {uploading ? 'Processing...' : 'Start Bid'}
                </button>
            </div>
        </div>
    )
}

export default Home
