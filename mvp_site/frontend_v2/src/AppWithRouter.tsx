import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { LandingPage } from './pages/LandingPage'
import { CampaignListPage } from './pages/CampaignListPage'
import { CampaignPage } from './pages/CampaignPage'
import { CampaignCreationPage } from './pages/CampaignCreationPage'
import { useAuth } from './hooks/useAuth'
// import { MockModeToggle } from './components/MockModeToggle'

export default function AppWithRouter() {
  const { user, loading, signInWithGoogle } = useAuth()

  // Removed test mode check for real production mode
  // const isTestMode = new URLSearchParams(window.location.search).get('test_mode') === 'true'

  return (
    <Router>
      <div className="min-h-screen">
        {/* Test Mode Indicator - Removed for real production mode */}
        {/* {isTestMode && (
          <div className="fixed top-4 right-4 z-50 bg-yellow-500/90 text-black px-3 py-1 rounded-lg text-sm font-medium shadow-lg">
            🧪 TEST MODE
          </div>
        )} */}

        <Routes>
          <Route path="/" element={
            loading ? (
              // Show loading screen while checking auth - no welcome page flash
              // Use SAME background as campaigns page to eliminate purple flash
              <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                  <h3 className="text-white text-xl">Checking authentication...</h3>
                </div>
              </div>
            ) : user ? (
              // User authenticated - redirect to campaigns
              <Navigate to="/campaigns" replace />
            ) : (
              // User not authenticated - show welcome page
              <LandingPage
                user={user}
                loading={loading}
                onSignIn={signInWithGoogle}
              />
            )
          } />

          <Route path="/campaigns" element={
            loading ? (
              <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                  <h3 className="text-white text-xl">Loading...</h3>
                </div>
              </div>
            ) : user ? <CampaignListPage /> : <Navigate to="/" replace />
          } />

          <Route path="/campaigns/create" element={
            loading ? (
              <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                  <h3 className="text-white text-xl">Loading...</h3>
                </div>
              </div>
            ) : user ? <CampaignCreationPage /> : <Navigate to="/" replace />
          } />

          <Route path="/campaigns/:campaignId" element={
            loading ? (
              <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                  <h3 className="text-white text-xl">Loading...</h3>
                </div>
              </div>
            ) : user ? <CampaignPage /> : <Navigate to="/" replace />
          } />

          <Route path="/campaign/:id" element={
            loading ? (
              <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                  <h3 className="text-white text-xl">Loading...</h3>
                </div>
              </div>
            ) : user ? <CampaignPage /> : <Navigate to="/" replace />
          } />

          {/* REMOVED: Character creation route - character creation happens in-game */}
        </Routes>

        {/* Mock Mode Toggle - Removed for real production mode */}
        {/* <MockModeToggle /> */}
      </div>
    </Router>
  )
}
