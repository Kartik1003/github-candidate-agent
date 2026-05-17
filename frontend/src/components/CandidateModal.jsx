export default function CandidateModal({ candidate: c, onClose }) {
    const breakdown = c.scoring?.breakdown || {}
    const pros = (c.scoring?.pros || "").split("|").filter(Boolean)
    const cons = (c.scoring?.cons || "").split("|").filter(Boolean)

    return (
        <div 
            className="animate-in"
            onClick={onClose}
            style={{
                position: "fixed", inset: 0, background: "rgba(0, 0, 0, 0.6)",
                backdropFilter: "blur(8px)",
                display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000
            }}>
            <div 
                className="glass-panel"
                onClick={e => e.stopPropagation()}
                style={{
                    padding: 40, width: "90%", maxWidth: 700, maxHeight: "90vh", 
                    overflowY: "auto", position: "relative"
                }}>

                <button onClick={onClose}
                    style={{
                        position: "absolute", top: 20, right: 24,
                        background: "var(--surface-high)", border: "1px solid var(--border-ghost)", width: 32, height: 32,
                        borderRadius: "50%", cursor: "pointer", display: "flex", 
                        alignItems: "center", justifyContent: "center", color: "var(--text-muted)", transition: "all 0.2s"
                    }}>✕</button>

                {/* Header */}
                <div style={{ marginBottom: 32 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 12 }}>
                         <div style={{ 
                            width: 60, height: 60, borderRadius: "50%", 
                            background: `linear-gradient(135deg, var(--secondary-color), var(--primary-dim))`,
                            display: "flex", alignItems: "center", justifyContent: "center",
                            fontSize: 24, fontWeight: 600, color: "white",
                            boxShadow: "0 8px 20px rgba(208, 149, 255, 0.2)"
                        }}>
                            {c.name[0]}
                        </div>
                        <div>
                            <h2 style={{ margin: 0, fontSize: 24, fontFamily: "var(--font-display)", color: "var(--text-main)" }}>{c.name}</h2>
                            <a href={`https://github.com/${c.login}`} target="_blank"
                                style={{ fontSize: 14, color: "var(--secondary-color)", textDecoration: "none", fontWeight: 600 }}>
                                github.com/{c.login}
                            </a>
                        </div>
                    </div>
                    <p style={{ margin: 0, color: "var(--text-muted)", fontSize: 15, lineHeight: 1.6 }}>{c.bio}</p>
                </div>

                {/* Score breakdown */}
                <div style={{ marginBottom: 32 }}>
                    <h3 style={{ fontSize: 14, fontFamily: "var(--font-display)", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 16 }}>Technical Breakdown</h3>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                        {Object.entries(breakdown).map(([key, val]) => (
                            <div key={key} style={{ padding: "16px", background: "var(--surface-high)", borderRadius: "var(--border-radius)", border: "1px solid var(--border-ghost)" }}>
                                <div style={{ fontSize: 11, fontWeight: 700, fontFamily: "var(--font-display)", color: "var(--text-muted)", marginBottom: 8, textTransform: "uppercase", letterSpacing: "1px" }}>
                                    {key.replace(/_/g, " ")}
                                </div>
                                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                    <div style={{ flex: 1, height: 6, background: "var(--surface-low)", borderRadius: 3, overflow: "hidden" }}>
                                        <div style={{
                                            width: `${(val || 0) * 100}%`, height: "100%",
                                            background: "var(--primary-color)", borderRadius: 3,
                                            boxShadow: "0 0 10px rgba(208, 149, 255, 0.5)"
                                        }} />
                                    </div>
                                    <span style={{ fontSize: 14, fontWeight: 700, color: "var(--text-main)", minWidth: 32 }}>
                                        {((val || 0) * 100).toFixed(0)}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Pros & Cons */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 32 }}>
                    <div style={{ padding: 20, background: "rgba(64, 206, 243, 0.1)", borderRadius: "var(--border-radius)", border: "1px solid rgba(64, 206, 243, 0.2)" }}>
                        <h3 style={{ fontSize: 12, fontWeight: 700, fontFamily: "var(--font-display)", color: "var(--secondary-color)", marginBottom: 16, textTransform: "uppercase", letterSpacing: "1px" }}>Strengths</h3>
                        {pros.map((p, i) => (
                            <div key={i} style={{ fontSize: 14, color: "var(--text-main)", marginBottom: 8, display: "flex", gap: 8 }}>
                                <span>✨</span> {p.trim()}
                            </div>
                        ))}
                    </div>
                    <div style={{ padding: 20, background: "rgba(255, 164, 76, 0.1)", borderRadius: "var(--border-radius)", border: "1px solid rgba(255, 164, 76, 0.2)" }}>
                        <h3 style={{ fontSize: 12, fontWeight: 700, fontFamily: "var(--font-display)", color: "#ffa44c", marginBottom: 16, textTransform: "uppercase", letterSpacing: "1px" }}>Considerations</h3>
                        {cons.map((p, i) => (
                            <div key={i} style={{ fontSize: 14, color: "var(--text-main)", marginBottom: 8, display: "flex", gap: 8 }}>
                                <span style={{opacity: 0.8}}>⚠️</span> {p.trim()}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Projects */}
                {(c.projects || []).length > 0 && (
                    <div style={{ marginBottom: 32 }}>
                        <h3 style={{ fontSize: 14, fontFamily: "var(--font-display)", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 16 }}>Key Projects</h3>
                        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                            {c.projects.map((p, i) => (
                                <div key={i} 
                                    className="float-hover"
                                    style={{
                                        padding: "16px 20px", background: "var(--surface-high)",
                                        borderRadius: "var(--border-radius)", border: "1px solid var(--border-ghost)"
                                    }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                        <div style={{ fontWeight: 600, fontSize: 15, color: "var(--text-main)" }}>{p.name}</div>
                                        {p.stars > 0 && <span style={{ fontSize: 12, color: "#ffa44c" }}>★ {p.stars}</span>}
                                    </div>
                                    {p.description && (
                                        <div style={{ fontSize: 13, color: "var(--text-muted)", margin: "6px 0", lineHeight: 1.5 }}>{p.description}</div>
                                    )}
                                    <div style={{ fontSize: 12, color: "var(--secondary-color)", fontWeight: 600 }}>
                                        {(p.languages || []).join(" • ")}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Footer Links */}
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap", borderTop: "1px solid var(--border-ghost)", paddingTop: 24 }}>
                    {c.links?.linkedin && (
                        <a href={c.links.linkedin} target="_blank"
                            className="float-hover"
                            style={{
                                padding: "10px 24px", background: "rgba(0, 119, 181, 0.2)", color: "#0077b5", border: "1px solid rgba(0, 119, 181, 0.4)",
                                borderRadius: 6, fontSize: 14, fontWeight: 600, textDecoration: "none"
                            }}>
                            View LinkedIn
                        </a>
                    )}
                    {c.links?.portfolio && (
                        <a href={c.links.portfolio} target="_blank"
                            className="float-hover"
                            style={{
                                padding: "10px 24px", background: "linear-gradient(135deg, var(--primary-color), var(--primary-dim))", color: "#fff",
                                borderRadius: 6, fontSize: 14, fontWeight: 600, textDecoration: "none", boxShadow: "0 4px 15px rgba(208, 149, 255, 0.3)"
                            }}>
                            Portfolio Website
                        </a>
                    )}
                </div>
            </div>
        </div>
    )
}