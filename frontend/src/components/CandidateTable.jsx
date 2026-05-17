import { useNavigate } from "react-router-dom"

const DOMAIN_COLORS = {
    frontend: { bg: "rgba(64, 206, 243, 0.15)", color: "var(--secondary-color)" },
    backend: { bg: "rgba(208, 149, 255, 0.15)", color: "var(--primary-color)" },
    ai_ml: { bg: "rgba(255, 164, 76, 0.15)", color: "#ffa44c" },
    data_engineering: { bg: "rgba(208, 149, 255, 0.15)", color: "var(--primary-color)" },
    devops: { bg: "rgba(64, 206, 243, 0.15)", color: "var(--secondary-color)" },
    mobile: { bg: "rgba(255, 164, 76, 0.15)", color: "#ffa44c" },
    full_stack: { bg: "rgba(208, 149, 255, 0.15)", color: "var(--primary-color)" },
}

export default function CandidateTable({ candidates, shortlisted, onToggleShortlist }) {
    const navigate = useNavigate()

    if (!candidates.length)
        return (
            <div className="glass-panel" style={{ padding: 60, textAlign: "center" }}>
                <p style={{ color: "var(--text-muted)", fontSize: 16 }}>No candidates found in this category.</p>
            </div>
        )

    return (
        <div className="glass-panel" style={{ overflow: "hidden" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
                <thead>
                    <tr style={{ background: "var(--surface-high)", borderBottom: "1px solid var(--border-ghost)" }}>
                        <th style={{ padding: "16px 20px", width: 40 }}>
                            <input type="checkbox"
                                style={{ transform: "scale(1.2)", cursor: "pointer", accentColor: "var(--primary-color)" }}
                                onChange={e => candidates.forEach(c => {
                                    if (e.target.checked !== shortlisted.has(c.login)) onToggleShortlist(c.login)
                                })}
                            />
                        </th>
                        {["Rank", "Candidate", "Domain", "Score", "Languages", "Links", "Insight", "🔬", "📋"].map(h => (
                            <th key={h} style={{
                                padding: "16px 14px", fontWeight: 600, fontFamily: "var(--font-display)",
                                color: "var(--text-muted)", textAlign: "left", textTransform: "uppercase", fontSize: 11, letterSpacing: "1px"
                            }}>
                                {h}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {candidates.map((c, idx) => {
                        const dc = DOMAIN_COLORS[c.category?.primary_domain] || { bg: "var(--surface-high)", color: "var(--text-main)" }
                        const checked = shortlisted.has(c.login)
                        return (
                            <tr key={c.login}
                                className="float-hover"
                                style={{
                                    borderBottom: "1px solid var(--border-ghost)",
                                    background: checked ? "rgba(208, 149, 255, 0.1)" : "transparent",
                                    animation: `fadeIn 0.4s ease-out both ${idx * 0.05}s`,
                                    cursor: "pointer"
                                }}
                                onClick={() => navigate(`/candidate/${c.login}`)}
                            >

                                <td style={{ padding: "16px 20px" }}
                                    onClick={e => e.stopPropagation()}>
                                    <input type="checkbox" checked={checked}
                                        style={{ transform: "scale(1.2)", cursor: "pointer", accentColor: "var(--primary-color)" }}
                                        onChange={() => onToggleShortlist(c.login)} />
                                </td>

                                <td style={{ padding: "16px 14px", color: "var(--text-muted)", fontWeight: 600, fontSize: 12 }}>
                                    #{c.rank}
                                </td>

                                <td style={{ padding: "16px 14px" }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                        <div style={{ 
                                            width: 36, height: 36, borderRadius: "50%", 
                                            background: `linear-gradient(135deg, var(--secondary-color), var(--primary-dim))`,
                                            display: "flex", alignItems: "center", justifyContent: "center",
                                            fontSize: 14, fontWeight: 600, color: "white"
                                        }}>
                                            {c.name[0]}
                                        </div>
                                        <div>
                                            <div style={{ fontWeight: 600, color: "var(--text-main)" }}>{c.name}</div>
                                            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>@{c.login}</div>
                                        </div>
                                    </div>
                                </td>

                                <td style={{ padding: "16px 14px" }}>
                                    <span style={{
                                        ...dc, padding: "5px 12px", borderRadius: 4,
                                        fontSize: 11, fontWeight: 600, letterSpacing: "0.3px", border: `1px solid ${dc.color}`
                                    }}>
                                        {(c.category?.primary_domain || "").replace(/_/g, " ").toUpperCase()}
                                    </span>
                                </td>

                                <td style={{ padding: "16px 14px" }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                        <span style={{ fontWeight: 700, fontSize: 15, color: "var(--primary-color)" }}>
                                            {((c.scoring?.score || 0) * 100).toFixed(0)}
                                        </span>
                                        <div style={{ width: 40, height: 4, background: "var(--surface-high)", borderRadius: 2, overflow: "hidden" }}>
                                            <div style={{
                                                width: `${(c.scoring?.score || 0) * 100}%`,
                                                height: "100%", background: "var(--primary-color)", borderRadius: 2
                                            }} />
                                        </div>
                                    </div>
                                </td>

                                <td style={{ padding: "16px 14px", color: "var(--text-muted)", fontSize: 12, fontWeight: 500 }}>
                                    {(c.activity?.top_languages || []).slice(0, 2).join(", ")}
                                </td>

                                <td style={{ padding: "16px 14px" }}>
                                    <div style={{ display: "flex", gap: 6 }}>
                                        {c.links?.linkedin && (
                                            <a href={c.links.linkedin} target="_blank" onClick={e => e.stopPropagation()}
                                                className="float-hover"
                                                style={{
                                                    fontSize: 10, padding: "4px 8px", background: "rgba(0, 119, 181, 0.2)",
                                                    color: "#0077b5", border: "1px solid rgba(0, 119, 181, 0.4)", borderRadius: 4, textDecoration: "none",
                                                    fontWeight: 600
                                                }}>IN</a>
                                        )}
                                        {c.links?.portfolio && (
                                            <a href={c.links.portfolio} target="_blank" onClick={e => e.stopPropagation()}
                                                className="float-hover"
                                                style={{
                                                    fontSize: 10, padding: "4px 8px", background: "rgba(64, 206, 243, 0.1)",
                                                    color: "var(--secondary-color)", border: "1px solid rgba(64, 206, 243, 0.3)", borderRadius: 4, textDecoration: "none",
                                                    fontWeight: 600
                                                }}>WEB</a>
                                        )}
                                    </div>
                                </td>

                                <td style={{ padding: "16px 14px", fontSize: 12, color: "var(--text-muted)", maxWidth: 200, fontStyle: "italic" }}>
                                    "{(c.scoring?.pros || "").split("|")[0]?.trim()}"
                                </td>

                                <td style={{ padding: "12px 8px" }} onClick={e => e.stopPropagation()}>
                                    <button
                                        onClick={() => navigate(`/enrich/${c.login}`)}
                                        className="float-hover"
                                        title="Deep Analysis — commit pattern, code quality, live projects"
                                        style={{
                                            padding: "5px 10px", borderRadius: 6, fontSize: 12,
                                            background: "rgba(208,149,255,0.08)", color: "var(--primary-color)",
                                            border: "1px solid rgba(208,149,255,0.25)", fontWeight: 600,
                                            cursor: "pointer",
                                        }}
                                    >
                                        🔬
                                    </button>
                                </td>

                                <td style={{ padding: "12px 8px" }} onClick={e => e.stopPropagation()}>
                                    <button
                                        onClick={() => navigate(`/profile/${c.login}`)}
                                        className="float-hover"
                                        title="CEO Report — red flags, collaboration, growth"
                                        style={{
                                            padding: "5px 10px", borderRadius: 6, fontSize: 12,
                                            background: "rgba(29,158,117,0.08)", color: "#1D9E75",
                                            border: "1px solid rgba(29,158,117,0.2)", fontWeight: 600,
                                            cursor: "pointer",
                                        }}
                                    >
                                        📋
                                    </button>
                                </td>
                            </tr>
                        )
                    })}
                </tbody>
            </table>
        </div>
    )
}