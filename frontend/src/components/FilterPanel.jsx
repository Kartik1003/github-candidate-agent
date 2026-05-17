const DOMAINS = ["", "frontend", "backend", "ai_ml", "data_engineering", "devops", "mobile", "full_stack"]

export default function FilterPanel({ filters, setFilters, stats }) {
    return (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <div>
                <label style={{ fontSize: 11, fontWeight: 700, fontFamily: "var(--font-display)", color: "var(--text-muted)", display: "block", marginBottom: 8, textTransform: "uppercase", letterSpacing: "1px" }}>Domain</label>
                <select value={filters.domain}
                    onChange={e => setFilters(f => ({ ...f, domain: e.target.value }))}
                    style={{
                        width: "100%", padding: "10px 14px", borderRadius: "var(--border-radius)", border: "1px solid var(--border-ghost)",
                        fontSize: 14, background: "var(--surface-high)", cursor: "pointer", outline: "none", color: "var(--text-main)",
                        fontFamily: "var(--font-body)"
                    }}>
                    {DOMAINS.map(d => (
                        <option key={d} value={d}>{d ? d.replace(/_/g, " ") : "All Categories"}</option>
                    ))}
                </select>
            </div>

            <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                    <label style={{ fontSize: 11, fontWeight: 700, fontFamily: "var(--font-display)", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>Min Match Score</label>
                    <span style={{ fontSize: 12, fontWeight: 600, color: "var(--primary-color)" }}>{(filters.min_score * 100).toFixed(0)}%</span>
                </div>
                <input type="range" min="0" max="1" step="0.05"
                    value={filters.min_score}
                    onChange={e => setFilters(f => ({ ...f, min_score: parseFloat(e.target.value) }))}
                    style={{ width: "100%", height: 4, cursor: "pointer", accentColor: "var(--primary-color)", background: "var(--surface-high)", outline: "none", borderRadius: 2 }} />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <label style={{
                    fontSize: 13, display: "flex", alignItems: "center",
                    gap: 10, cursor: "pointer", color: "var(--text-main)", fontWeight: 500
                }}>
                    <input type="checkbox" checked={filters.has_linkedin}
                        style={{ width: 16, height: 16, accentColor: "var(--primary-color)", cursor: "pointer" }}
                        onChange={e => setFilters(f => ({ ...f, has_linkedin: e.target.checked }))} />
                    Has LinkedIn
                </label>
                <label style={{
                    fontSize: 13, display: "flex", alignItems: "center",
                    gap: 10, cursor: "pointer", color: "var(--text-main)", fontWeight: 500
                }}>
                    <input type="checkbox" checked={filters.has_cv}
                        style={{ width: 16, height: 16, accentColor: "var(--primary-color)", cursor: "pointer" }}
                        onChange={e => setFilters(f => ({ ...f, has_cv: e.target.checked }))} />
                    Has CV / Portfolio
                </label>
            </div>

            {stats.domains && (
                <div style={{ marginTop: 10, borderTop: "1px solid var(--border-ghost)", paddingTop: 20 }}>
                    <label style={{ fontSize: 11, fontWeight: 700, fontFamily: "var(--font-display)", color: "var(--text-muted)", display: "block", marginBottom: 12, textTransform: "uppercase", letterSpacing: "1px" }}>Domain Stats</label>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                        {Object.entries(stats.domains).map(([d, count]) => (
                            <div key={d}
                                className="float-hover"
                                onClick={() => setFilters(f => ({ ...f, domain: f.domain === d ? "" : d }))}
                                style={{
                                    fontSize: 11, padding: "6px 12px", 
                                    background: filters.domain === d ? "linear-gradient(135deg, var(--primary-color), var(--primary-dim))" : "var(--surface-high)",
                                    border: `1px solid ${filters.domain === d ? "transparent" : "var(--border-ghost)"}`,
                                    color: filters.domain === d ? "#fff" : "var(--text-main)",
                                    borderRadius: 6, cursor: "pointer", fontWeight: 600,
                                    boxShadow: filters.domain === d ? "0 4px 12px rgba(208, 149, 255, 0.3)" : "none"
                                }}>
                                {d.replace(/_/g, " ")} <span style={{ opacity: filters.domain === d ? 0.9 : 0.5, marginLeft: 4 }}>{count}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}