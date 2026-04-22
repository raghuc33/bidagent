import { useState } from 'react'
import { runComplianceCheck } from '../services/api'
import LoadingSpinner from './LoadingSpinner'

const STATUS_STYLES = {
    addressed: 'bg-green-100 text-green-700',
    partial: 'bg-yellow-100 text-yellow-700',
    missing: 'bg-red-100 text-red-600',
    not_checked: 'bg-gray-100 text-gray-500',
}

const STATUS_LABELS = {
    addressed: 'Addressed',
    partial: 'Partial',
    missing: 'Missing',
    not_checked: 'Not checked',
}

function ComplianceMatrix({ drafts, onClose }) {
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [filter, setFilter] = useState('all')

    const handleRun = async () => {
        setLoading(true)
        setError(null)
        try {
            const data = await runComplianceCheck(drafts)
            setResult(data)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const filtered = result?.requirements?.filter(r => {
        if (filter === 'all') return true
        return r.status === filter
    }) || []

    return (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
                    <div>
                        <h2 className="text-lg font-bold">Compliance Matrix</h2>
                        <p className="text-xs text-gray-400">Checks tender requirements against your bid drafts</p>
                    </div>
                    <div className="flex items-center gap-3">
                        {!result && (
                            <button
                                onClick={handleRun}
                                disabled={loading}
                                className="px-4 py-2 bg-blue-500 text-white rounded-md text-sm font-medium hover:bg-blue-600 disabled:opacity-50"
                            >
                                {loading ? 'Analyzing...' : 'Run Check'}
                            </button>
                        )}
                        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto px-6 py-4">
                    {loading && (
                        <div className="flex flex-col items-center justify-center py-16 gap-3">
                            <LoadingSpinner size="lg" />
                            <p className="text-gray-500 text-sm">Extracting requirements and checking coverage...</p>
                        </div>
                    )}

                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-md p-4 text-red-600 text-sm">{error}</div>
                    )}

                    {result && (
                        <>
                            {/* Summary bar */}
                            <div className="grid grid-cols-4 gap-3 mb-6">
                                <div className="bg-gray-50 rounded-lg p-3 text-center">
                                    <div className="text-2xl font-bold">{result.total}</div>
                                    <div className="text-xs text-gray-400">Requirements</div>
                                </div>
                                <div className="bg-green-50 rounded-lg p-3 text-center">
                                    <div className="text-2xl font-bold text-green-600">{result.addressed}</div>
                                    <div className="text-xs text-gray-400">Addressed</div>
                                </div>
                                <div className="bg-yellow-50 rounded-lg p-3 text-center">
                                    <div className="text-2xl font-bold text-yellow-600">{result.partial || 0}</div>
                                    <div className="text-xs text-gray-400">Partial</div>
                                </div>
                                <div className="bg-red-50 rounded-lg p-3 text-center">
                                    <div className="text-2xl font-bold text-red-600">{result.gaps}</div>
                                    <div className="text-xs text-gray-400">Gaps</div>
                                </div>
                            </div>

                            {/* Coverage bar */}
                            <div className="mb-6">
                                <div className="flex justify-between text-xs text-gray-500 mb-1">
                                    <span>Coverage</span>
                                    <span>{result.coverage_pct}%</span>
                                </div>
                                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full rounded-full transition-all ${
                                            result.coverage_pct >= 80 ? 'bg-green-500'
                                            : result.coverage_pct >= 50 ? 'bg-yellow-500'
                                            : 'bg-red-500'
                                        }`}
                                        style={{ width: `${result.coverage_pct}%` }}
                                    />
                                </div>
                            </div>

                            {/* Filter tabs */}
                            <div className="flex gap-1 mb-4">
                                {['all', 'missing', 'partial', 'addressed'].map(f => (
                                    <button
                                        key={f}
                                        onClick={() => setFilter(f)}
                                        className={`px-3 py-1 text-xs rounded-full ${
                                            filter === f ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                        }`}
                                    >
                                        {f === 'all' ? `All (${result.total})` : `${STATUS_LABELS[f]} (${result.requirements.filter(r => r.status === f).length})`}
                                    </button>
                                ))}
                            </div>

                            {/* Requirements table */}
                            <div className="space-y-2">
                                {filtered.map((req, i) => (
                                    <div key={req.id || i} className="border border-gray-200 rounded-lg p-3">
                                        <div className="flex items-start justify-between gap-3">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${STATUS_STYLES[req.status] || STATUS_STYLES.not_checked}`}>
                                                        {STATUS_LABELS[req.status] || 'Unknown'}
                                                    </span>
                                                    <span className="text-[10px] text-gray-400 uppercase">{req.category}</span>
                                                    {req.criticality === 'mandatory' && (
                                                        <span className="text-[10px] text-red-500 font-medium">Mandatory</span>
                                                    )}
                                                </div>
                                                <p className="text-sm text-gray-800">{req.requirement}</p>
                                                {req.notes && (
                                                    <p className="text-xs text-gray-500 mt-1">{req.notes}</p>
                                                )}
                                            </div>
                                            {req.addressed_in && (
                                                <span className="text-[10px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded shrink-0">
                                                    {req.addressed_in}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Re-run button */}
                            <div className="mt-6 text-center">
                                <button
                                    onClick={handleRun}
                                    disabled={loading}
                                    className="px-4 py-2 bg-gray-100 text-gray-600 rounded-md text-sm hover:bg-gray-200 disabled:opacity-50"
                                >
                                    Re-run Check
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}

export default ComplianceMatrix
