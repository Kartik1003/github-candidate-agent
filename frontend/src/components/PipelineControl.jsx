import { useState, useRef } from "react"

export default function PipelineControl({ onComplete }) {
    const [running, setRunning] = useState(false)
    const [logs, setLogs] = useState([])
    const [showLog, setShowLog] = useState(false)
    const logsEndRef = useRef(null)

    const startPipeline = () => {
        setRunning(true)
        setLogs(["Connecting to pipeline...\n"])
        setShowLog(true)

        const ws = new WebSocket("ws://localhost:8000/ws/run-pipeline")

        ws.onmessage = (e) => {
            setLogs(prev => [...prev, e.data])
            logsEndRef.current?.scrollIntoView({ behavior: "smooth" })
        }

        ws.onclose = () => {
            setRunning(false)
            onComplete()
        }

        ws.onerror = () => {
            setLogs(prev => [...prev, "Connection error — is the backend running?\n"])
            setRunning(false)
        }
    }

    return (
        <>
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                {logs.length > 0 && (
                    <button 
                        className="float-hover"
                        onClick={() => setShowLog(v => !v)}
                        style={{
                            padding: "10px 16px", background: "var(--surface-high)", border: "1px solid var(--border-ghost)",
                            borderRadius: "var(--border-radius)", cursor: "pointer", fontSize: 13, color: "var(--text-muted)",
                            fontWeight: 600, fontFamily: "var(--font-body)"
                        }}>
                        {showLog ? "📁 Hide log" : "📄 Show log"}
                    </button>
                )}
                <button 
                    className="float-hover"
                    onClick={startPipeline} disabled={running}
                    style={{
                        padding: "12px 24px", 
                        background: running ? "var(--surface-high)" : "linear-gradient(135deg, var(--primary-color), var(--primary-dim))",
                        color: running ? "var(--secondary-color)" : "#fff", border: `1px solid ${running ? "var(--secondary-color)" : "transparent"}`, 
                        borderRadius: "var(--border-radius)",
                        cursor: running ? "not-allowed" : "pointer",
                        fontSize: 14, fontWeight: 600, fontFamily: "var(--font-display)",
                        boxShadow: running ? "none" : "0 4px 15px rgba(208, 149, 255, 0.3)"
                    }}>
                    {running ? "✨ Scanning..." : "🚀 Initiate Search"}
                </button>
            </div>

            {showLog && (
                <div style={{
                    position: "fixed", bottom: 24, right: 24, width: 440, maxHeight: 280,
                    background: "#111", color: "#00ff88", fontFamily: "monospace",
                    fontSize: 12, padding: 16, borderRadius: 12,
                    overflowY: "auto", zIndex: 999, boxShadow: "0 8px 32px rgba(0,0,0,0.3)"
                }}>
                    <div style={{
                        display: "flex", justifyContent: "space-between",
                        marginBottom: 10, paddingBottom: 8, borderBottom: "1px solid #333"
                    }}>
                        <span style={{ color: "#666", fontSize: 11 }}>PIPELINE LOG</span>
                        <button onClick={() => setShowLog(false)}
                            style={{
                                background: "none", border: "none", color: "#555",
                                cursor: "pointer", fontSize: 14
                            }}>✕</button>
                    </div>
                    {logs.map((l, i) => <div key={i} style={{ marginBottom: 2 }}>{l}</div>)}
                    <div ref={logsEndRef} />
                </div>
            )}
        </>
    )
}