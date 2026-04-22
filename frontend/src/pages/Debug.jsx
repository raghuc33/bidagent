import { useState, useEffect } from 'react'

function Debug() {
    const [verification, setVerification] = useState({
        vercelServing: false,
        envVars: {},
        cors: null,
        fastapiReachable: null,
        loading: true
    })

    useEffect(() => {
        const checkAll = async () => {
            // Check if Vercel is serving (we're running, so yes)
            const vercelServing = true

            // Get env vars
            const envVars = {
                VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'Not set',
                NODE_ENV: import.meta.env.MODE || 'Not set',
                // Show all VITE_ prefixed env vars
                ...Object.keys(import.meta.env)
                    .filter(key => key.startsWith('VITE_'))
                    .reduce((acc, key) => {
                        acc[key] = import.meta.env[key]
                        return acc
                    }, {})
            }

            // Get API URL from env or default
            const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

            // Test CORS and FastAPI reachability
            let cors = null
            let fastapiReachable = null

            try {
                const response = await fetch(`${apiUrl}/health`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                })

                if (response.ok) {
                    const data = await response.json()
                    fastapiReachable = { success: true, data }
                    cors = { success: true, message: 'CORS is configured correctly' }
                } else {
                    fastapiReachable = { success: false, error: `HTTP ${response.status}` }
                    cors = { success: false, error: `HTTP ${response.status}` }
                }
            } catch (error) {
                fastapiReachable = { success: false, error: error.message }
                cors = { success: false, error: error.message }
            }

            setVerification({
                vercelServing,
                envVars,
                cors,
                fastapiReachable,
                loading: false
            })
        }

        checkAll()
    }, [])

    const StatusBadge = ({ success, error }) => {
        if (success === null) return <span className="status pending">Checking...</span>
        if (success) return <span className="status success">✓ Success</span>
        return <span className="status error">✗ Failed: {error}</span>
    }

    if (verification.loading) {
        return (
            <div style={{ padding: '2rem', textAlign: 'center' }}>
                <h1>BidAgent Frontend Verification</h1>
                <p>Checking configuration...</p>
            </div>
        )
    }

    return (
        <div style={{
            maxWidth: '800px',
            margin: '0 auto',
            padding: '2rem',
            fontFamily: 'system-ui, sans-serif'
        }}>
            <h1>BidAgent Frontend Verification</h1>

            <div style={{
                display: 'grid',
                gap: '1.5rem',
                marginTop: '2rem'
            }}>
                {/* Vercel Serving Check */}
                <div style={{
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    padding: '1.5rem',
                    backgroundColor: '#f9f9f9'
                }}>
                    <h2 style={{ marginTop: 0 }}>1. Is Vercel serving FE?</h2>
                    <StatusBadge success={verification.vercelServing} />
                    <p style={{ marginTop: '0.5rem', color: '#666' }}>
                        If you can see this page, Vercel is serving the frontend.
                    </p>
                </div>

                {/* Env Vars */}
                <div style={{
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    padding: '1.5rem',
                    backgroundColor: '#f9f9f9'
                }}>
                    <h2 style={{ marginTop: 0 }}>2. Are env vars injected?</h2>
                    <div style={{ marginTop: '1rem' }}>
                        {Object.keys(verification.envVars).length > 0 ? (
                            <div style={{
                                backgroundColor: '#fff',
                                padding: '1rem',
                                borderRadius: '4px',
                                fontFamily: 'monospace',
                                fontSize: '0.9rem'
                            }}>
                                {Object.entries(verification.envVars).map(([key, value]) => (
                                    <div key={key} style={{ marginBottom: '0.5rem' }}>
                                        <strong>{key}:</strong> {String(value)}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p style={{ color: '#666' }}>No VITE_ prefixed environment variables found.</p>
                        )}
                    </div>
                </div>

                {/* CORS Check */}
                <div style={{
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    padding: '1.5rem',
                    backgroundColor: '#f9f9f9'
                }}>
                    <h2 style={{ marginTop: 0 }}>3. Is CORS correct?</h2>
                    <StatusBadge
                        success={verification.cors?.success}
                        error={verification.cors?.error || verification.cors?.message}
                    />
                    {verification.cors?.success && (
                        <p style={{ marginTop: '0.5rem', color: '#666' }}>
                            {verification.cors.message}
                        </p>
                    )}
                </div>

                {/* FastAPI Reachability */}
                <div style={{
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    padding: '1.5rem',
                    backgroundColor: '#f9f9f9'
                }}>
                    <h2 style={{ marginTop: 0 }}>4. Is FastAPI reachable?</h2>
                    <StatusBadge
                        success={verification.fastapiReachable?.success}
                        error={verification.fastapiReachable?.error}
                    />
                    {verification.fastapiReachable?.success && (
                        <div style={{ marginTop: '0.5rem' }}>
                            <p style={{ color: '#666', marginBottom: '0.5rem' }}>Response:</p>
                            <pre style={{
                                backgroundColor: '#fff',
                                padding: '1rem',
                                borderRadius: '4px',
                                fontSize: '0.9rem',
                                overflow: 'auto'
                            }}>
                                {JSON.stringify(verification.fastapiReachable.data, null, 2)}
                            </pre>
                        </div>
                    )}
                </div>
            </div>

            <style>{`
        .status {
          display: inline-block;
          padding: 0.5rem 1rem;
          border-radius: 4px;
          font-weight: 600;
          font-size: 0.9rem;
        }
        .status.success {
          background-color: #d4edda;
          color: #155724;
        }
        .status.error {
          background-color: #f8d7da;
          color: #721c24;
        }
        .status.pending {
          background-color: #fff3cd;
          color: #856404;
        }
      `}</style>
        </div>
    )
}

export default Debug
