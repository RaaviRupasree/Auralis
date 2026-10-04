import { useEffect, useRef, useState } from 'react'
import './App.css'

const backendUrl = 'http://127.0.0.1:8000'

function waitForIceGathering(peerConnection) {
  if (peerConnection.iceGatheringState === 'complete') {
    return Promise.resolve()
  }

  return new Promise((resolve) => {
    const onGatheringStateChange = () => {
      if (peerConnection.iceGatheringState === 'complete') {
        peerConnection.removeEventListener(
          'icegatheringstatechange',
          onGatheringStateChange,
        )
        resolve()
      }
    }

    peerConnection.addEventListener(
      'icegatheringstatechange',
      onGatheringStateChange,
    )
  })
}

function releaseMedia(peerConnectionRef, mediaStreamRef) {
  peerConnectionRef.current?.close()
  peerConnectionRef.current = null
  mediaStreamRef.current?.getTracks().forEach((track) => track.stop())
  mediaStreamRef.current = null
}

function App() {
  const peerConnectionRef = useRef(null)
  const mediaStreamRef = useRef(null)
  const [permissionState, setPermissionState] = useState('not requested')
  const [connectionState, setConnectionState] = useState('disconnected')
  const [microphoneActive, setMicrophoneActive] = useState(false)
  const [isStarting, setIsStarting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    return () => releaseMedia(peerConnectionRef, mediaStreamRef)
  }, [])

  const stopMicrophone = () => {
    releaseMedia(peerConnectionRef, mediaStreamRef)
    setMicrophoneActive(false)
    setConnectionState('disconnected')
    setError('')
  }

  const startMicrophone = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setPermissionState('unavailable')
      setConnectionState('failed')
      setError('Microphone access is unavailable in this browser context.')
      return
    }

    setIsStarting(true)
    setPermissionState('requesting')
    setConnectionState('connecting')
    setError('')

    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      })
      mediaStreamRef.current = mediaStream
      setPermissionState('granted')
      setMicrophoneActive(true)

      const peerConnection = new RTCPeerConnection()
      peerConnectionRef.current = peerConnection
      mediaStream.getAudioTracks().forEach((track) => {
        peerConnection.addTrack(track, mediaStream)
      })

      peerConnection.onconnectionstatechange = () => {
        setConnectionState(peerConnection.connectionState)
        if (peerConnection.connectionState === 'failed') {
          setError('WebRTC connection failed. Check that the backend is running.')
        }
      }

      const offer = await peerConnection.createOffer()
      await peerConnection.setLocalDescription(offer)
      await waitForIceGathering(peerConnection)

      const response = await fetch(`${backendUrl}/offer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sdp: peerConnection.localDescription.sdp,
          type: peerConnection.localDescription.type,
        }),
      })

      if (!response.ok) {
        const result = await response.json().catch(() => ({}))
        throw new Error(
          result.detail || `WebRTC signaling failed (${response.status}).`,
        )
      }

      const answer = await response.json()
      await peerConnection.setRemoteDescription(answer)
    } catch (startError) {
      if (!mediaStreamRef.current) {
        setPermissionState(
          startError.name === 'NotAllowedError' ? 'denied' : 'unavailable',
        )
      }
      releaseMedia(peerConnectionRef, mediaStreamRef)
      setMicrophoneActive(false)
      setConnectionState('failed')
      setError(startError.message || 'Could not start the microphone connection.')
    } finally {
      setIsStarting(false)
    }
  }

  const permissionLabel = {
    'not requested': 'Not requested',
    requesting: 'Requesting permission',
    granted: 'Granted',
    denied: 'Denied',
    unavailable: 'Unavailable',
  }[permissionState]

  const connectionLabel = {
    disconnected: 'Disconnected',
    connecting: 'Connecting',
    connected: 'Connected',
    failed: 'Failed',
    closed: 'Disconnected',
  }[connectionState] || connectionState

  return (
    <div className="auralis-shell">
      <main className="audio-panel">
        <div className="panel-kicker">
          <span className="panel-mark" aria-hidden="true" />
          LOCAL AUDIO LINK
        </div>
        <h1 className="auralis-title">Auralis</h1>
        <p className="panel-description">Microphone connection</p>

        <button
          className={`microphone-button${microphoneActive ? ' is-active' : ''}`}
          type="button"
          onClick={microphoneActive ? stopMicrophone : startMicrophone}
          disabled={isStarting}
          aria-pressed={microphoneActive}
        >
          <span className="button-indicator" aria-hidden="true" />
          {isStarting
            ? permissionState === 'requesting'
              ? 'Requesting Microphone...'
              : 'Connecting...'
            : microphoneActive
              ? 'Microphone Active'
              : 'Start Microphone'}
        </button>

        <div className="connection-details" aria-live="polite">
          <div className="status-row">
            <span>Microphone permission</span>
            <strong>{permissionLabel}</strong>
          </div>
          <div className="status-row">
            <span>Connection Status</span>
            <strong className={`connection-value is-${connectionState}`}>
              <span className="status-dot" aria-hidden="true" />
              {connectionLabel}
            </strong>
          </div>
        </div>

        {error && <p className="connection-error" role="alert">{error}</p>}
      </main>
    </div>
  )
}

export default App
