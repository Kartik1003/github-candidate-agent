import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import axios from "axios"
import { ArrowLeft, ExternalLink, Github, Linkedin, Briefcase } from "lucide-react"

const API = "http://localhost:8000"

export default function CandidateDetails() {
    const { login } = useParams()
    const navigate = useNavigate()
    const [c, setCandidate] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchCandidate = async () => {
            try {
                const res = await axios.get(`${API}/candidates/${login}`)
                setCandidate(res.data)
            } catch (e) {
                console.error(e)
            } finally {
                setLoading(false)
            }
        }
        fetchCandidate()
    }, [login])

    if (loading) return (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "var(--text-muted)" }}>
            Loading candidate details...
        </div>
    )

    if (!c) return (
        <div style={{ padding: 40, textAlign: "center" }}>
            <h2>Candidate not found</h2>
            <button onClick={() => navigate("/")} style={{ color: "var(--primary-color)", background: "none", border: "none", cursor: "pointer" }}>
                Return to Dashboard
            </button>
        </div>
    )

    const breakdown = c.scoring?.breakdown || {}
    const pros = (c.scoring?.pros || "").split("|").filter(Boolean)
    const cons = (c.scoring?.cons || "").split("|").filter(Boolean)

    return (
        <div className="animate-in" style={{ maxWidth: 900, margin: "0 auto", padding: "40px 24px" }}>
            <button onClick={() => navigate("/")} 
                className="float-hover"
                style={{ 
                    display: "flex", alignItems: "center", gap: 8, color: "var(--text-muted)", 
                    background: "var(--surface-high)", padding: "10px 16px", borderRadius: 8, 
                    marginBottom: 32, fontSize: 14, fontWeight: 600 
                }}>
                <ArrowLeft size={16} /> Back to Dashboard
            </button>

            <div className="glass-panel" style={{ padding: 40 }}>
                {/* Header */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 40 }}>
                    <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
                        <div style={{ 
                            width: 80, height: 80, borderRadius: "50%", 
                            background: `linear-gradient(135deg, var(--secondary-color), var(--primary-dim))`,
                            display: "flex", alignItems: "center", justifyContent: "center",
                            fontSize: 32, fontWeight: 600, color: "white",
                            boxShadow: "0 8px 20px rgba(208, 149, 255, 0.2)"
                        }}>
                            {c.name[0]}
                        </div>
                        <div>
                            <h1 style={{ fontSize: 32, marginBottom: 4 }}>{c.name}</h1>
                            <div style={{ display: "flex", gap: 16, color: "var(--text-muted)", fontSize: 16 }}>
                                <span style={{ display: "flex", alignItems: "center", gap: 4 }}><Github size={16} /> @{c.login}</span>
                                {c.location && <span>📍 {c.location}</span>}
                            </div>
                        </div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                        <div style={{ fontSize: 12, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>Match Score</div>
                        <div style={{ fontSize: 40, fontWeight: 800, color: "var(--primary-color)" }}>
                            {((c.scoring?.score || 0) * 100).toFixed(0)}
                        </div>
                    </div>
                </div>

                <p style={{ fontSize: 18, lineHeight: 1.6, color: "var(--text-main)", marginBottom: 40, borderLeft: "4px solid var(--border-ghost)", paddingLeft: 24 }}>
                    {c.bio || "No bio provided."}
                </p>

                {/* Technical Breakdown */}
                <div style={{ marginBottom: 48 }}>
                    <h3 style={{ fontSize: 14, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 20 }}>Technical Breakdown</h3>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 20 }}>
                        {Object.entries(breakdown).map(([key, val]) => (
                            <div key={key} style={{ padding: 20, background: "var(--surface-high)", borderRadius: 12, border: "1px solid var(--border-ghost)" }}>
                                <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 12, textTransform: "uppercase" }}>{key.replace(/_/g, " ")}</div>
                                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                    <div style={{ flex: 1, height: 6, background: "var(--surface-low)", borderRadius: 3, overflow: "hidden" }}>
                                        <div style={{ width: `${(val || 0) * 100}%`, height: "100%", background: "var(--primary-color)", borderRadius: 3 }} />
                                    </div>
                                    <span style={{ fontWeight: 700 }}>{((val || 0) * 100).toFixed(0)}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Insights */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 48 }}>
                    <div style={{ padding: 24, background: "rgba(64, 206, 243, 0.05)", borderRadius: 16, border: "1px solid rgba(64, 206, 243, 0.2)" }}>
                        <h3 style={{ color: "var(--secondary-color)", fontSize: 14, textTransform: "uppercase", marginBottom: 16 }}>Strengths</h3>
                        {pros.map((p, i) => <div key={i} style={{ marginBottom: 10, display: "flex", gap: 8 }}><span>✨</span> {p.trim()}</div>)}
                    </div>
                    <div style={{ padding: 24, background: "rgba(255, 164, 76, 0.05)", borderRadius: 16, border: "1px solid rgba(255, 164, 76, 0.2)" }}>
                        <h3 style={{ color: "#ffa44c", fontSize: 14, textTransform: "uppercase", marginBottom: 16 }}>Considerations</h3>
                        {cons.map((p, i) => <div key={i} style={{ marginBottom: 10, display: "flex", gap: 8 }}><span>⚠️</span> {p.trim()}</div>)}
                    </div>
                </div>

                {/* Projects */}
                {(c.projects || []).length > 0 && (
                    <div style={{ marginBottom: 48 }}>
                        <h3 style={{ fontSize: 14, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 20 }}>Key Projects</h3>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                            {c.projects.map((p, i) => (
                                <div key={i} className="float-hover" style={{ padding: 20, background: "var(--surface-high)", borderRadius: 12, border: "1px solid var(--border-ghost)" }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                                        <div style={{ fontWeight: 700 }}>{p.name}</div>
                                        <span style={{ color: "#ffa44c" }}>★ {p.stars}</span>
                                    </div>
                                    <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 12, height: 40, overflow: "hidden" }}>{p.description}</p>
                                    <div style={{ fontSize: 12, color: "var(--secondary-color)", fontWeight: 600 }}>{(p.languages || []).join(" • ")}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Footer Links */}
                <div style={{ display: "flex", gap: 16, borderTop: "1px solid var(--border-ghost)", paddingTop: 32 }}>
                    <a href={`https://github.com/${c.login}`} target="_blank" className="float-hover" style={{ padding: "12px 24px", background: "var(--surface-high)", color: "var(--text-main)", borderRadius: 8, textDecoration: "none", fontWeight: 600, display: "flex", alignItems: "center", gap: 8 }}>
                        <Github size={18} /> GitHub Profile
                    </a>
                    {c.links?.linkedin && (
                        <a href={c.links.linkedin} target="_blank" className="float-hover" style={{ padding: "12px 24px", background: "rgba(0, 119, 181, 0.2)", color: "#0077b5", borderRadius: 8, textDecoration: "none", fontWeight: 600, display: "flex", alignItems: "center", gap: 8 }}>
                            <Linkedin size={18} /> LinkedIn
                        </a>
                    )}
                    {c.links?.portfolio && (
                        <a href={c.links.portfolio} target="_blank" className="float-hover" style={{ padding: "12px 24px", background: "linear-gradient(135deg, var(--primary-color), var(--primary-dim))", color: "white", borderRadius: 8, textDecoration: "none", fontWeight: 600, display: "flex", alignItems: "center", gap: 8 }}>
                            <ExternalLink size={18} /> Portfolio
                        </a>
                    )}
                </div>
            </div>
        </div>
    )
}
