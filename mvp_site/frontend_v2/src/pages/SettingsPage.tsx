import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { ArrowLeft, Settings, Check, AlertTriangle, Loader2 } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { apiService } from '../services/api.service'

// Only models that support code_execution + JSON mode together
type GeminiModel = 'gemini-3-pro-preview' | 'gemini-2.0-flash'

const GEMINI_MODEL_MAPPING: Record<string, GeminiModel> = {
  'gemini-3-pro-preview': 'gemini-3-pro-preview',
  'gemini-2.0-flash': 'gemini-2.0-flash',
  'gemini-2.5-flash': 'gemini-2.0-flash',
  'gemini-2.5-pro': 'gemini-2.0-flash',
  'pro-2.5': 'gemini-2.0-flash',
  'flash-2.5': 'gemini-2.0-flash'
}

// Users allowed to see Gemini 3 Pro option (expensive model)
const GEMINI_3_ALLOWED_USERS = ['jleechan@gmail.com', 'jleechantest@gmail.com']

interface UserSettings {
  geminiModel: GeminiModel
  debugMode: boolean
}

export function SettingsPage() {
  const navigate = useNavigate()
  const { user, signOut } = useAuth()

  // Check if current user can access Gemini 3
  const allowedGeminiEmails = useMemo(
    () => GEMINI_3_ALLOWED_USERS.map((email) => email.toLowerCase()),
    [],
  )

  const canUseGemini3 = !!(
    user?.email && allowedGeminiEmails.includes(user.email.toLowerCase())
  )

  const [settings, setSettings] = useState<UserSettings>({
    geminiModel: 'gemini-2.0-flash',
    debugMode: false
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState<string>('')
  const [errorMessage, setErrorMessage] = useState<string>('')
  const hasLoadedRef = useRef(false)
  const isInitialLoadRef = useRef(true)

  const loadSettings = useCallback(async () => {
    setLoading(true)
    setErrorMessage('')

    try {
      const data = await apiService.getUserSettings()
      // Load saved model, default to gemini-2.0-flash
      const mappedModel = GEMINI_MODEL_MAPPING[data.gemini_model] || 'gemini-2.0-flash'
      // Non-premium users always get 2.0-flash regardless of saved setting, but keep premium for allowlisted
      const model: GeminiModel =
        mappedModel === 'gemini-3-pro-preview' && !canUseGemini3
          ? 'gemini-2.0-flash'
          : mappedModel
      setSettings({
        geminiModel: model,
        debugMode: data.debug_mode || false
      })
    } catch (error) {
      console.error('Error loading settings:', error)
      setErrorMessage('Failed to load settings. Using defaults.')
    } finally {
      setLoading(false)
      hasLoadedRef.current = true // Mark as loaded after first successful load
      // Set initial load to false after a brief delay to prevent auto-save trigger
      setTimeout(() => {
        isInitialLoadRef.current = false
      }, 100)
    }
  }, [canUseGemini3])

  // Load settings once auth state is available
  useEffect(() => {
    if (!user) return
    loadSettings()
  }, [user, loadSettings])

  const saveSettings = useCallback(async () => {
    setSaving(true)
    setSaveMessage('')
    setErrorMessage('')

    try {
      // Convert camelCase to snake_case for API
      const apiSettings = {
        gemini_model: settings.geminiModel,
        debug_mode: settings.debugMode
      }
      await apiService.updateUserSettings(apiSettings)
      setSaveMessage('Settings saved successfully!')
      setTimeout(() => setSaveMessage(''), 3000)
    } catch (error) {
      console.error('Error saving settings:', error)
      setErrorMessage(error instanceof Error ? error.message : 'Failed to save settings. Please try again.')
    } finally {
      setSaving(false)
    }
  }, [settings.geminiModel, settings.debugMode])

  // Auto-save when settings change (debounced) - only after initial load
  useEffect(() => {
    // Skip auto-save during initial load or before component has loaded once
    if (loading || !hasLoadedRef.current || isInitialLoadRef.current) return

    const timeoutId = setTimeout(() => {
      saveSettings()
    }, 1000) // Debounce by 1 second

    return () => clearTimeout(timeoutId)
  }, [settings.geminiModel, settings.debugMode, loading, saveSettings])

  const handleModelChange = (model: GeminiModel) => {
    setSettings(prev => ({ ...prev, geminiModel: model }))
  }

  const handleDebugModeChange = (checked: boolean) => {
    setSettings(prev => ({ ...prev, debugMode: checked }))
  }

  // Apply settings-view body class when component mounts
  useEffect(() => {
    document.body.classList.add('settings-view')
    return () => {
      document.body.classList.remove('settings-view')
    }
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-6 py-8">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <Button
              variant="ghost"
              size="sm"
              className="text-purple-200 hover:text-white hover:bg-purple-500/20"
              onClick={() => navigate('/campaigns')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Campaigns
            </Button>
          </div>

          {/* Settings Card */}
          <Card className="bg-black/60 backdrop-blur-sm border-purple-500/30">
            <CardHeader className="pb-4">
              <CardTitle className="text-white text-3xl flex items-center gap-3">
                <Settings className="w-8 h-8 text-purple-400" />
                Settings
              </CardTitle>
              {user?.email && (
                <p className="text-purple-200">
                  Signed in as: <span className="text-white">{user.email}</span>
                </p>
              )}
            </CardHeader>

            <CardContent className="space-y-8">
              {/* AI Model Selection */}
              <div>
                <h3 className="text-white text-xl mb-2">AI Model</h3>
                <p className="text-purple-200 mb-4">
                  {canUseGemini3 ? 'Choose your preferred Gemini model' : 'Your AI model for all interactions'}
                </p>

                <div className="space-y-3">
                  {canUseGemini3 && (
                    <label className="flex items-start gap-3 p-4 rounded-lg border border-purple-500/30 hover:border-purple-400/50 cursor-pointer transition-colors">
                      <input
                        type="radio"
                        name="geminiModel"
                        value="gemini-3-pro-preview"
                        checked={settings.geminiModel === 'gemini-3-pro-preview'}
                        onChange={() => handleModelChange('gemini-3-pro-preview')}
                        className="mt-1 text-purple-500 focus:ring-purple-500 focus:ring-2"
                      />
                      <div>
                        <div className="text-white font-semibold">Gemini 3 Pro Preview</div>
                        <div className="text-purple-200 text-sm">Premium model with advanced reasoning (higher cost)</div>
                      </div>
                    </label>
                  )}

                  <label className={`flex items-start gap-3 p-4 rounded-lg border border-purple-500/30 ${canUseGemini3 ? 'hover:border-purple-400/50 cursor-pointer' : 'bg-purple-900/20'} transition-colors`}>
                    {canUseGemini3 ? (
                      <input
                        type="radio"
                        name="geminiModel"
                        value="gemini-2.0-flash"
                        checked={settings.geminiModel === 'gemini-2.0-flash'}
                        onChange={() => handleModelChange('gemini-2.0-flash')}
                        className="mt-1 text-purple-500 focus:ring-purple-500 focus:ring-2"
                      />
                    ) : null}
                    <div>
                      <div className="text-white font-semibold">Gemini 2.0 Flash {!canUseGemini3 && '(Default)'}</div>
                      <div className="text-purple-200 text-sm">Fast responses with code execution and dice roll support</div>
                    </div>
                  </label>
                </div>
              </div>

              <hr className="border-purple-500/30" />

              {/* Debug Mode */}
              <div>
                <h3 className="text-white text-xl mb-2">Debug Mode</h3>
                <p className="text-purple-200 mb-4">Enable debug mode for detailed logging and troubleshooting</p>

                <label className="flex items-start gap-3 p-4 rounded-lg border border-purple-500/30 hover:border-purple-400/50 cursor-pointer transition-colors">
                  <input
                    type="checkbox"
                    checked={settings.debugMode}
                    onChange={(e) => handleDebugModeChange(e.target.checked)}
                    className="mt-1 text-purple-500 focus:ring-purple-500 focus:ring-2 rounded"
                  />
                  <div>
                    <div className="text-white font-semibold">Enable Debug Mode</div>
                    <div className="text-purple-200 text-sm">Shows detailed logs and debugging information</div>
                  </div>
                </label>
              </div>

              <hr className="border-purple-500/30" />

              {/* Account Management */}
              <div>
                <h3 className="text-white text-xl mb-2">Account Management</h3>
                <p className="text-purple-200 mb-4">Manage your WorldArchitect.AI account</p>

                <div className="space-y-3">
                  <Button
                    variant="destructive"
                    size="lg"
                    onClick={() => signOut()}
                    className="w-full bg-red-600 hover:bg-red-700 text-white font-semibold"
                  >
                    Sign Out
                  </Button>
                </div>
              </div>

              {/* Status Messages */}
              {saveMessage && (
                <div className="flex items-center gap-2 p-3 bg-green-500/20 border border-green-500/30 rounded-lg">
                  <Check className="w-5 h-5 text-green-400" />
                  <span className="text-green-300">{saveMessage}</span>
                </div>
              )}

              {errorMessage && (
                <div className="flex items-center gap-2 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                  <span className="text-red-300">{errorMessage}</span>
                </div>
              )}

              {saving && (
                <div className="flex items-center justify-center gap-2 p-3 bg-blue-500/20 border border-blue-500/30 rounded-lg">
                  <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
                  <span className="text-blue-300">Saving settings...</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
