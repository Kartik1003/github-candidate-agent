import { useState, useEffect } from "react"
import axios from "axios"
import { useNavigate } from "react-router-dom"

const API = "http://localhost:8000"

const SIGNAL_LABELS = {
  "same_blog_url":       { label: "Same blog/portfolio URL", weight: "🔴 High" },
  "same_name":           { label: "Same full name",          weight: "🟡 Medium" },
  "same_location_and_name": { label: "Same location + name", weight: "🟡 Medium" },
  "shared_repos":        { label: "Shared repo names",       weight: "🟡 Medium" },
  "bio_similarity":      { label: "Similar bio text",        weight: "🟢 Low" },
}

function parseSignal(sig) {
  for (const [key, meta] of Object.entries(SIGNAL_LABELS)) {
    if (sig.startsWith(key)) return { ...meta, raw: sig }
  }
  return { label: sig, weight: "⚪ Unknown", raw: sig }
}

function ConfidenceMeter({ value }) {
  const pct = Math.round(value * 100)
  const color = pct >= 80 ? "#E64D4D" : pct >= 60 ? "#E6A817" : "#1D9E75"
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div style={{ flex: 1, height: 6, borderRadius: 3, background: "var(--surface-high)", overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", borderRadius: 3, background: color, transition: "width 0.5s ease" }} />
      </div>
      <span style={{ fontSize: 13, fontWeight: 700, color, minWidth: 36 }}>{pct}%</span>
    </div>
  )
}

export default function DuplicateDetector() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [clusters, setClusters] = useState(null)
  const [total, setTotal] = useState(0)

  const run = async () => {
    setLoading(true)
    setClusters(null)
    try {
      const res = await axios.get(`${API}/duplicates`)
      setClusters(res.data.clusters || [])
      setTotal(res.data.count || 0)
    } catch (e) {
      setClusters([])
    }
    setLoading(false)
  }

  useEffect(() => { run() }, [])

  return (
    <div className="animate-in" style={{ maxWidth: 900, margin: "0 auto", padding: "40px 24px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 32 }}>
        <button onClick={() => navigate("/")} style={{ padding: "8px 16px", borderRadius: 6, background: "var(--surface-high)", color: "var(--text-muted)", border: "1px solid var(--border-ghost)", fontSize: 13 }}>← Back</button>
        <div>
          <h1 style={{ fontSize: 26 }}>👥 Duplicate <span style={{ color: "var(--primary-color)", fontWeight: 400 }}>Detector</span></h1>
          <p style={{ color: "var(--text-muted)", fontSize: 14, marginTop: 4 }}>
            Finds candidates who may have multiple GitHub accounts
          </p>
        </div>
        <button onClick={run} disabled={loading} style={{ marginLeft: "auto", padding: "10px 20px", borderRadius: 8, background: "linear-gradient(135deg, var(--primary-color), var(--primary-dim))", color: "#fff", fontWeight: 700, fontSize: 14, boxShadow: "0 4px 15px rgba(208,149,255,0.25)" }}>
          {loading ? "🔍 Scanning..." : "🔄 Re-scan"}
        </button>
      </div>

      {/* How It Works */}
      <div className="glass-panel" style={{ padding: "16px 20px", marginBottom: 24 }}>
        <div style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.7 }}>
          <strong style={{ color: "var(--text-main)" }}>How it works:</strong> Compares bio text similarity, shared repo names,
          same blog URL, location + name matching across all {total} candidates in cache.
          Results are purely heuristic — always verify manually.
        </div>
      </div>

      {loading ? (
        <div className="glass-panel" style={{ padding: 80, textAlign: "center" }}>
          <div style={{ width: 40, height: 40, border: "4px solid rgba(208,149,255,0.2)", borderTopColor: "var(--primary-color)", borderRadius: "50%", margin: "0 auto 16px", animation: "spin 1s linear infinite" }} />
          <p style={{ color: "var(--text-muted)" }}>Scanning candidates for duplicates...</p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      ) : clusters !== null && (
        clusters.length === 0 ? (
          <div className="glass-panel" style={{ padding: 60, textAlign: "center" }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>✅</div>
            <p style={{ color: "#1D9E75", fontWeight: 600, fontSize: 16 }}>No duplicate accounts detected!</p>
            <p style={{ color: "var(--text-muted)", fontSize: 14, marginTop: 8 }}>All candidates appear to be unique individuals.</p>
          </div>
        ) : (
          <div>
            <div style={{ marginBottom: 20, fontSize: 14, color: "#E6A817", fontWeight: 600 }}>
              ⚠️ Found {clusters.length} potential duplicate cluster{clusters.length !== 1 ? "s" : ""}
            </div>
            {clusters.map((cluster, i) => (
              <div key={i} className="glass-panel" style={{ marginBottom: 16, overflow: "hidden" }}>
                {/* Header */}
                <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border-ghost)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text-main)" }}>
                    Cluster #{i + 1}
                  </div>
                  <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Confidence</span>
                    <div style={{ width: 140 }}><ConfidenceMeter value={cluster.confidence} /></div>
                  </div>
                </div>

                <div style={{ padding: "16px 20px" }}>
                  {/* Accounts */}
                  <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 16 }}>
                    <div style={{ padding: "8px 14px", borderRadius: 8, background: "rgba(208,149,255,0.1)", border: "1px solid rgba(208,149,255,0.3)" }}>
                      <div style={{ fontSize: 11, color: "var(--primary-color)", fontWeight: 700, marginBottom: 2 }}>PRIMARY</div>
                      <a href={`https://github.com/${cluster.primary}`} target="_blank" rel="noreferrer"
                        style={{ fontSize: 14, color: "var(--text-main)", fontWeight: 600, textDecoration: "none" }}>
                        @{cluster.primary}
                      </a>
                    </div>
                    {cluster.aliases.map(alias => (
                      <div key={alias} style={{ padding: "8px 14px", borderRadius: 8, background: "rgba(230,77,77,0.08)", border: "1px solid rgba(230,77,77,0.25)" }}>
                        <div style={{ fontSize: 11, color: "#E64D4D", fontWeight: 700, marginBottom: 2 }}>POSSIBLE ALIAS</div>
                        <a href={`https://github.com/${alias}`} target="_blank" rel="noreferrer"
                          style={{ fontSize: 14, color: "var(--text-main)", fontWeight: 600, textDecoration: "none" }}>
                          @{alias}
                        </a>
                      </div>
                    ))}
                  </div>

                  {/* Signals */}
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
                    {cluster.signals.map(sig => {
                      const meta = parseSignal(sig)
                      return (
                        <span key={sig} title={meta.raw} style={{
                          fontSize: 11, padding: "4px 10px", borderRadius: 20,
                          background: "var(--surface-high)", color: "var(--text-muted)",
                          border: "1px solid var(--border-ghost)", fontWeight: 600,
                        }}>
                          {meta.weight} {meta.label}
                        </span>
                      )
                    })}
                  </div>

                  {/* Shared repos */}
                  {cluster.shared_repos?.length > 0 && (
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      Shared repos: {cluster.shared_repos.map(r => (
                        <span key={r} style={{ marginLeft: 6, background: "var(--surface-high)", padding: "2px 8px", borderRadius: 4, fontSize: 11 }}>{r}</span>
                      ))}
                    </div>
                  )}

                  {/* Actions */}
                  <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
                    <button onClick={() => navigate(`/candidate/${cluster.primary}`)}
                      style={{ padding: "7px 14px", borderRadius: 6, background: "rgba(208,149,255,0.1)", color: "var(--primary-color)", border: "1px solid rgba(208,149,255,0.3)", fontSize: 12, fontWeight: 600 }}>
                      View Primary →
                    </button>
                    {cluster.aliases[0] && (
                      <button onClick={() => navigate(`/compare?a=${cluster.primary}&b=${cluster.aliases[0]}`)}
                        style={{ padding: "7px 14px", borderRadius: 6, background: "rgba(64,206,243,0.08)", color: "var(--secondary-color)", border: "1px solid rgba(64,206,243,0.2)", fontSize: 12, fontWeight: 600 }}>
                        ⚖️ Compare Side by Side
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  )
}
