import { useState, useEffect } from "react"
import axios from "axios"
import { useNavigate } from "react-router-dom"

const API = "http://localhost:8000"
const MIN_LABELS = 50

export default function MLTraining() {
  const navigate = useNavigate()
  const [candidates, setCandidates] = useState([])
  const [labelCounts, setLabelCounts] = useState({ good: 0, bad: 0 })
  const [modelStatus, setModelStatus] = useState({ model_exists: false })
  const [training, setTraining] = useState(false)
  const [trainResult, setTrainResult] = useState(null)
  const [pendingLabels, setPendingLabels] = useState({}) // login -> 'good'|'bad'
  const [saving, setSaving] = useState({}) // login -> bool

  const totalLabeled = (labelCounts.good || 0) + (labelCounts.bad || 0)
  const progress = Math.min(100, Math.round((totalLabeled / MIN_LABELS) * 100))
  const canTrain = totalLabeled >= MIN_LABELS

  useEffect(() => {
    fetchCandidates()
    fetchLabelCounts()
    fetchModelStatus()
  }, [])

  const fetchCandidates = async () => {
    try {
      const res = await axios.get(`${API}/candidates`)
      setCandidates(res.data)
    } catch (e) { console.error(e) }
  }

  const fetchLabelCounts = async () => {
    try {
      const res = await axios.get(`${API}/label-counts`)
      setLabelCounts(res.data)
    } catch (e) { console.error(e) }
  }

  const fetchModelStatus = async () => {
    try {
      const res = await axios.get(`${API}/model-status`)
      setModelStatus(res.data)
    } catch (e) { console.error(e) }
  }

  const handleLabel = async (login, label) => {
    setSaving(s => ({ ...s, [login]: true }))
    try {
      await axios.post(`${API}/candidates/${login}/label`, { label })
      setPendingLabels(p => ({ ...p, [login]: label }))
      await fetchLabelCounts()
    } catch (e) { console.error(e) }
    setSaving(s => ({ ...s, [login]: false }))
  }

  const handleTrain = async () => {
    setTraining(true)
    setTrainResult(null)
    try {
      const res = await axios.post(`${API}/train`)
      setTrainResult(res.data)
      await fetchModelStatus()
      await fetchLabelCounts()
    } catch (e) {
      setTrainResult({ error: e?.response?.data?.error || "Training failed" })
    }
    setTraining(false)
  }

  const getLabel = (c) => pendingLabels[c.login] || c.label || null

  const labelColor = (lbl) => ({
    good: { bg: "rgba(29, 158, 117, 0.15)", border: "rgba(29, 158, 117, 0.5)", text: "#1D9E75" },
    bad:  { bg: "rgba(230, 77, 77, 0.12)", border: "rgba(230, 77, 77, 0.4)", text: "#E64D4D" },
  })[lbl] || {}

  return (
    <div className="animate-in" style={{ maxWidth: 1200, margin: "0 auto", padding: "40px 24px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 32 }}>
        <button
          onClick={() => navigate("/")}
          style={{ padding: "8px 16px", borderRadius: 6, background: "var(--surface-high)", color: "var(--text-muted)", border: "1px solid var(--border-ghost)", fontSize: 13 }}
        >
          ← Back
        </button>
        <div>
          <h1 style={{ fontSize: 26, color: "var(--text-main)" }}>
            🧠 ML Training <span style={{ color: "var(--primary-color)", fontWeight: 400 }}>Studio</span>
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: 14, marginTop: 4 }}>
            Label candidates as Good or Bad to train the XGBoost scoring model
          </p>
        </div>
      </div>

      {/* Stats + Train Button Row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr auto", gap: 16, marginBottom: 32 }}>
        {[
          { label: "✅ Good", value: labelCounts.good || 0, color: "#1D9E75" },
          { label: "❌ Bad",  value: labelCounts.bad || 0,  color: "#E64D4D" },
          { label: "📊 Total Labeled", value: totalLabeled, color: "var(--secondary-color)" },
        ].map(({ label, value, color }) => (
          <div key={label} className="glass-panel" style={{ padding: "20px 24px", textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color, fontFamily: "var(--font-display)" }}>{value}</div>
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4, fontWeight: 600 }}>{label}</div>
          </div>
        ))}
        <div className="glass-panel" style={{ padding: "20px 24px", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", minWidth: 160 }}>
          <button
            onClick={handleTrain}
            disabled={!canTrain || training}
            style={{
              padding: "12px 24px",
              background: canTrain ? "linear-gradient(135deg, var(--primary-color), var(--primary-dim))" : "var(--surface-high)",
              color: canTrain ? "#fff" : "var(--text-muted)",
              borderRadius: 8, fontWeight: 700, fontSize: 14,
              boxShadow: canTrain ? "0 4px 15px rgba(208, 149, 255, 0.35)" : "none",
              transition: "all 0.2s",
              cursor: canTrain && !training ? "pointer" : "not-allowed",
              width: "100%",
            }}
          >
            {training ? "⏳ Training..." : "🚀 Train Model"}
          </button>
          {!canTrain && (
            <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8, textAlign: "center" }}>
              Need {MIN_LABELS - totalLabeled} more labels
            </p>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="glass-panel" style={{ padding: "20px 24px", marginBottom: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-muted)" }}>
            Progress to training threshold
          </span>
          <span style={{ fontSize: 13, fontWeight: 700, color: canTrain ? "#1D9E75" : "var(--primary-color)" }}>
            {totalLabeled} / {MIN_LABELS} {canTrain ? "✅ Ready!" : ""}
          </span>
        </div>
        <div style={{ height: 8, borderRadius: 4, background: "var(--surface-high)", overflow: "hidden" }}>
          <div style={{
            height: "100%",
            width: `${progress}%`,
            borderRadius: 4,
            background: canTrain
              ? "linear-gradient(90deg, #1D9E75, #40cef3)"
              : "linear-gradient(90deg, var(--primary-dim), var(--primary-color))",
            transition: "width 0.6s ease",
          }} />
        </div>
      </div>

      {/* Model Status */}
      {modelStatus.model_exists && (
        <div style={{
          marginBottom: 24, padding: "14px 20px", borderRadius: 8,
          background: "rgba(29,158,117,0.1)", border: "1px solid rgba(29,158,117,0.3)",
          fontSize: 14, color: "#1D9E75", fontWeight: 600,
        }}>
          ✅ Trained model is active — new candidates will use XGBoost scoring
        </div>
      )}

      {/* Training Result */}
      {trainResult && (
        <div className="glass-panel" style={{ marginBottom: 24, padding: "20px 24px" }}>
          {trainResult.error ? (
            <p style={{ color: "#E64D4D", fontWeight: 600 }}>❌ {trainResult.error}</p>
          ) : trainResult.status === "insufficient_data" ? (
            <p style={{ color: "#E6A817", fontWeight: 600 }}>⚠️ {trainResult.message}</p>
          ) : (
            <div>
              <p style={{ fontWeight: 700, color: "#1D9E75", fontSize: 16, marginBottom: 12 }}>
                ✅ Model trained successfully! ({trainResult.model_type})
              </p>
              <div style={{ display: "flex", gap: 32, flexWrap: "wrap" }}>
                {[
                  ["Accuracy", `${(trainResult.accuracy * 100).toFixed(1)}%`],
                  ["Train samples", trainResult.train_size],
                  ["Test samples", trainResult.test_size],
                  ["Skipped", trainResult.skipped],
                ].map(([k, v]) => (
                  <div key={k}>
                    <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 2 }}>{k}</div>
                    <div style={{ fontSize: 20, fontWeight: 700, color: "var(--secondary-color)" }}>{v}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Candidate Table */}
      <div className="glass-panel" style={{ overflow: "hidden" }}>
        <div style={{ padding: "16px 24px", borderBottom: "1px solid var(--border-ghost)", fontSize: 13, color: "var(--text-muted)", fontWeight: 600 }}>
          {candidates.length} candidates — label each as Good or Bad
        </div>
        <div style={{ maxHeight: 520, overflowY: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "var(--surface-high)", position: "sticky", top: 0, zIndex: 1 }}>
                {["Rank", "Candidate", "Domain", "Score", "Languages", "Label"].map(h => (
                  <th key={h} style={{ padding: "12px 16px", textAlign: "left", fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "var(--text-muted)", borderBottom: "1px solid var(--border-ghost)" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {candidates.map((c, i) => {
                const lbl = getLabel(c)
                const colors = lbl ? labelColor(lbl) : {}
                const score = Math.round((c.scoring?.score || 0) * 100)
                return (
                  <tr
                    key={c.login}
                    style={{
                      borderBottom: "1px solid var(--border-ghost)",
                      background: lbl ? colors.bg : "transparent",
                      transition: "background 0.2s",
                    }}
                  >
                    <td style={{ padding: "12px 16px", fontSize: 13, color: "var(--text-muted)", fontWeight: 600 }}>#{i + 1}</td>
                    <td style={{ padding: "12px 16px" }}>
                      <div style={{ fontWeight: 600, fontSize: 14 }}>{c.name || c.login}</div>
                      <a href={`https://github.com/${c.login}`} target="_blank" rel="noreferrer"
                        style={{ fontSize: 12, color: "var(--secondary-color)", textDecoration: "none" }}>
                        @{c.login}
                      </a>
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <span style={{ fontSize: 11, padding: "4px 10px", borderRadius: 20, background: "var(--surface-high)", color: "var(--text-muted)", fontWeight: 600 }}>
                        {(c.category?.primary_domain || "").replace(/_/g, " ")}
                      </span>
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <span style={{ fontSize: 15, fontWeight: 700, color: score >= 60 ? "#1D9E75" : score >= 35 ? "#E6A817" : "#E64D4D" }}>
                        {score}
                      </span>
                    </td>
                    <td style={{ padding: "12px 16px", fontSize: 12, color: "var(--text-muted)" }}>
                      {(c.activity?.top_languages || []).slice(0, 3).join(", ")}
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      {lbl ? (
                        <span style={{ fontSize: 12, fontWeight: 700, color: colors.text, padding: "4px 12px", borderRadius: 6, border: `1px solid ${colors.border}`, background: colors.bg }}>
                          {lbl === "good" ? "✅ Good" : "❌ Bad"}
                        </span>
                      ) : (
                        <div style={{ display: "flex", gap: 8 }}>
                          {["good", "bad"].map(opt => (
                            <button
                              key={opt}
                              onClick={() => handleLabel(c.login, opt)}
                              disabled={saving[c.login]}
                              style={{
                                padding: "5px 14px", borderRadius: 6, fontSize: 12, fontWeight: 600,
                                background: opt === "good" ? "rgba(29,158,117,0.1)" : "rgba(230,77,77,0.1)",
                                color: opt === "good" ? "#1D9E75" : "#E64D4D",
                                border: `1px solid ${opt === "good" ? "rgba(29,158,117,0.3)" : "rgba(230,77,77,0.3)"}`,
                                cursor: saving[c.login] ? "not-allowed" : "pointer",
                                transition: "all 0.15s",
                              }}
                            >
                              {opt === "good" ? "✅" : "❌"} {opt}
                            </button>
                          ))}
                        </div>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
