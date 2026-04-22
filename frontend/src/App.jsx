import { BrowserRouter, Routes, Route } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home'
import BidBuilder from './pages/BidBuilder'
import Debug from './pages/Debug'
import Login from './pages/Login'
import Signup from './pages/Signup'

function App() {
    return (
        <ErrorBoundary>
            <BrowserRouter>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/signup" element={<Signup />} />
                    <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
                    <Route path="/bid" element={<ProtectedRoute><BidBuilder /></ProtectedRoute>} />
                    <Route path="/bid/:sessionId" element={<ProtectedRoute><BidBuilder /></ProtectedRoute>} />
                    <Route path="/debug" element={<Debug />} />
                </Routes>
            </BrowserRouter>
        </ErrorBoundary>
    )
}

export default App
