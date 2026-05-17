import { useState } from "react"
import axios from "axios"

const DEFAULT_SUBJECT = "Exciting opportunity — we'd love to connect"
const DEFAULT_BODY = `Hi {{name}},

I came across your GitHub profile and was genuinely impressed by your work in {{domain}}.

We are currently hiring for internship and full-time roles and think you could be a great fit based on your projects and contributions.

Would you be open to a quick 15-minute call this week to explore this further?

A few details about the opportunity:
- Role: Software Engineering Intern / Junior Developer
- Duration: 3-6 months (internship) or full-time
- Stipend/Salary: Competitive, based on your experience
- Mode: Remote / Hybrid

Your GitHub: {{github}}

Looking forward to hearing from you!

Best regards,
[Your Name]
[Your Company]
[Your Contact]`

export default function EmailComposer({ candidates, onClose, onSent }) {
    const [subject, setSubject] = useState(DEFAULT_SUBJECT)
    const [body, setBody] = useState(DEFAULT_BODY)
    const [sending, setSending] = useState(false)
    const [result, setResult] = useState(null)

    const handleSend = async () => {
        setSending(true)
        try {
            const res = await axios.post("http://localhost:8000/send-emails", {
                logins: candidates.map(c => c.login),
                subject,
                body,
            })
            setResult(res.data)
        } catch (e) {
            setResult({ error: e.message })
        }
        setSending(false)
    }

    return (
        <div 
            className="animate-in"
            style={{
                position: "fixed", inset: 0, background: "rgba(0, 0, 0, 0.6)",
                backdropFilter: "blur(8px)",
                display: "flex", alignItems: "center", justifyContent: "center", zIndex: 2000
            }}>
            <div 
                className="glass-panel"
                style={{
                    width: "90%", maxWidth: 750, maxHeight: "90vh", overflowY: "auto", padding: 40
                }}>

                {/* Header */}
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 32 }}>
                    <div>
                        <h2 style={{ margin: 0, fontSize: 22, fontFamily: "var(--font-display)", color: "var(--text-main)" }}>Recruitment Outreach</h2>
                        <p style={{ margin: "8px 0 0", fontSize: 14, color: "var(--text-muted)", fontFamily: "var(--font-body)" }}>
                            Personalizing outreach for {candidates.length} candidate{candidates.length !== 1 ? "s" : ""}
                        </p>
                    </div>
                    <button onClick={onClose}
                        style={{ background: "var(--surface-high)", border: "1px solid var(--border-ghost)", width: 32, height: 32, borderRadius: "50%", cursor: "pointer", color: "var(--text-muted)", transition: "all 0.2s" }}>
                        ✕
                    </button>
                </div>

                {/* Selected candidates chips */}
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 24 }}>
                    {candidates.map(c => (
                        <span key={c.login} style={{
                            padding: "6px 14px", background: "rgba(64, 206, 243, 0.1)",
                            color: "var(--secondary-color)", borderRadius: 6, fontSize: 12, fontWeight: 600,
                            border: "1px solid rgba(64, 206, 243, 0.3)", fontFamily: "var(--font-display)", letterSpacing: "0.5px"
                        }}>
                            {c.name || c.login}
                        </span>
                    ))}
                </div>

                {/* Template variables hint */}
                <div style={{
                    padding: "12px 16px", background: "var(--surface-high)", borderRadius: "var(--border-radius)",
                    marginBottom: 24, fontSize: 13, color: "var(--accent-color)", border: "1px solid var(--border-ghost)"
                }}>
                    <strong style={{ display: "block", marginBottom: 4, fontSize: 11, fontFamily: "var(--font-display)", textTransform: "uppercase", letterSpacing: "1px" }}>Available Tokens</strong>
                    <code style={{background: "var(--surface-low)", padding: "2px 6px", borderRadius: 4}}>{"{{name}}"}</code> • <code style={{background: "var(--surface-low)", padding: "2px 6px", borderRadius: 4}}>{"{{github}}"}</code> • 
                    <code style={{background: "var(--surface-low)", padding: "2px 6px", borderRadius: 4}}>{"{{domain}}"}</code> • <code style={{background: "var(--surface-low)", padding: "2px 6px", borderRadius: 4}}>{"{{score}}"}</code>
                </div>

                {/* Subject */}
                <div style={{ marginBottom: 20 }}>
                    <label style={{ fontSize: 11, fontWeight: 700, fontFamily: "var(--font-display)", color: "var(--text-muted)", display: "block", marginBottom: 8, textTransform: "uppercase", letterSpacing: "1px" }}>
                        Email Subject
                    </label>
                    <input value={subject} onChange={e => setSubject(e.target.value)}
                        style={{
                            width: "100%", padding: "12px 16px", borderRadius: "var(--border-radius)", border: "1px solid var(--border-ghost)",
                            fontSize: 14, outline: "none", background: "var(--surface-low)", color: "var(--text-main)", fontFamily: "var(--font-body)"
                        }} />
                </div>

                {/* Body */}
                <div style={{ marginBottom: 24 }}>
                    <label style={{ fontSize: 11, fontWeight: 700, fontFamily: "var(--font-display)", color: "var(--text-muted)", display: "block", marginBottom: 8, textTransform: "uppercase", letterSpacing: "1px" }}>
                        Message Template
                    </label>
                    <textarea value={body} onChange={e => setBody(e.target.value)} rows={12}
                        style={{
                            width: "100%", padding: "16px", borderRadius: "var(--border-radius)", border: "1px solid var(--border-ghost)",
                            fontSize: 14, fontFamily: "var(--font-body)", resize: "vertical",
                            lineHeight: 1.6, outline: "none", background: "var(--surface-low)", color: "var(--text-main)"
                        }} />
                </div>

                {/* Result message */}
                {result && (
                    <div style={{
                        padding: "14px 20px", borderRadius: "var(--border-radius)", marginBottom: 24,
                        background: result.error ? "rgba(255, 164, 76, 0.1)" : "rgba(64, 206, 243, 0.1)",
                        color: result.error ? "#ffa44c" : "var(--secondary-color)", fontSize: 14, fontWeight: 500,
                        border: result.error ? "1px solid rgba(255, 164, 76, 0.3)" : "1px solid rgba(64, 206, 243, 0.3)"
                    }}>
                        {result.error
                            ? `⚠️ Error: ${result.error}`
                            : `✨ Sent to ${result.sent} candidate${result.sent !== 1 ? "s" : ""} successfully.
                 ${result.failed > 0 ? `${result.failed} failed.` : ""}`
                        }
                    </div>
                )}

                {/* Actions */}
                <div style={{ display: "flex", justifyContent: "flex-end", gap: 12 }}>
                    <button 
                        className="float-hover"
                        onClick={onClose}
                        style={{
                            padding: "12px 24px", background: "var(--surface-high)", border: "1px solid var(--border-ghost)",
                            borderRadius: "var(--border-radius)", cursor: "pointer", fontSize: 14, color: "var(--text-muted)",
                            fontWeight: 600, fontFamily: "var(--font-body)"
                        }}>
                        Cancel
                    </button>
                    {result && !result.error ? (
                        <button 
                            className="float-hover"
                            onClick={onSent}
                            style={{
                                padding: "12px 32px", background: "linear-gradient(135deg, var(--primary-color), var(--primary-dim))", color: "#fff",
                                border: "none", borderRadius: "var(--border-radius)", cursor: "pointer", fontSize: 14, fontWeight: 600, fontFamily: "var(--font-display)",
                                boxShadow: "0 4px 15px rgba(208, 149, 255, 0.3)"
                            }}>
                            Done
                        </button>
                    ) : (
                        <button 
                            className="float-hover"
                            onClick={handleSend} disabled={sending}
                            style={{
                                padding: "12px 32px", background: sending ? "var(--surface-high)" : "linear-gradient(135deg, var(--primary-color), var(--primary-dim))",
                                color: sending ? "var(--secondary-color)" : "#fff", border: `1px solid ${sending ? "var(--secondary-color)" : "transparent"}`, borderRadius: "var(--border-radius)",
                                cursor: sending ? "not-allowed" : "pointer",
                                fontSize: 14, fontWeight: 600, fontFamily: "var(--font-display)",
                                boxShadow: sending ? "none" : "0 4px 15px rgba(208, 149, 255, 0.3)"
                            }}>
                            {sending ? "✨ Sending..." : `Send to ${candidates.length} Selected`}
                        </button>
                    )}
                </div>
            </div>
        </div>
    )
}