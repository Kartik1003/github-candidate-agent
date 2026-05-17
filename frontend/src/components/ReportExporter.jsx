import { useState } from "react"
import axios from "axios"

const API = "http://localhost:8000"

const labelStyle = {
  fontSize: 11, fontWeight: 700, fontFamily: "var(--font-display)",
  color: "var(--text-muted)", display: "block", marginBottom: 6,
  textTransform: "uppercase", letterSpacing: "1px",
}

const inputStyle = {
  width: "100%", padding: "9px 12px", borderRadius: "var(--border-radius)",
  border: "1px solid var(--border-ghost)", fontSize: 13,
  background: "var(--surface-high)", color: "var(--text-main)",
  fontFamily: "var(--font-body)", outline: "none", cursor: "pointer",
  colorScheme: "dark",
}

export default function ReportExporter() {
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [status, setStatus] = useState(null) // null | "sending" | "sent" | "error"
  const [result, setResult] = useState(null)

  const handleSend = async () => {
    if (!startDate || !endDate) {
      setStatus("error")
      setResult("Please select both start and end dates.")
      return
    }
    if (startDate > endDate) {
      setStatus("error")
      setResult("Start date must be before end date.")
      return
    }

    setStatus("sending")
    setResult(null)

    try {
      const res = await axios.post(`${API}/send-report`, {
        start_date: startDate,
        end_date: endDate,
      })
      setStatus("sent")
      setResult(`✅ Report sent! ${res.data.candidates} candidates (${res.data.date_range})`)
    } catch (e) {
      setStatus("error")
      const msg = e.response?.data?.error || e.message
      setResult(`❌ ${msg}`)
    }
  }

  const setToday = () => {
    const today = new Date().toISOString().split("T")[0]
    setStartDate(today)
    setEndDate(today)
    setStatus(null)
  }

  const setThisWeek = () => {
    const now = new Date()
    const day = now.getDay()
    const monday = new Date(now)
    monday.setDate(now.getDate() - (day === 0 ? 6 : day - 1))
    const sunday = new Date(monday)
    sunday.setDate(monday.getDate() + 6)
    setStartDate(monday.toISOString().split("T")[0])
    setEndDate(sunday.toISOString().split("T")[0])
    setStatus(null)
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>

      {/* Quick Presets */}
      <div style={{ display: "flex", gap: 6 }}>
        <button onClick={setToday} className="float-hover" style={{
          flex: 1, padding: "7px 0", borderRadius: 5, fontSize: 11,
          fontWeight: 700, cursor: "pointer", background: "var(--surface-high)",
          color: "var(--text-muted)", border: "1px solid var(--border-ghost)",
        }}>Today</button>
        <button onClick={setThisWeek} className="float-hover" style={{
          flex: 1, padding: "7px 0", borderRadius: 5, fontSize: 11,
          fontWeight: 700, cursor: "pointer", background: "var(--surface-high)",
          color: "var(--text-muted)", border: "1px solid var(--border-ghost)",
        }}>This Week</button>
      </div>

      {/* Date Range Inputs */}
      <div>
        <label style={labelStyle}>From</label>
        <input type="date" value={startDate} onChange={e => { setStartDate(e.target.value); setStatus(null) }}
          style={inputStyle} />
      </div>
      <div>
        <label style={labelStyle}>To</label>
        <input type="date" value={endDate} onChange={e => { setEndDate(e.target.value); setStatus(null) }}
          style={inputStyle} />
      </div>

      {/* Send Button */}
      <button onClick={handleSend} disabled={status === "sending"}
        className="float-hover"
        style={{
          padding: "11px 0", borderRadius: "var(--border-radius)",
          background: status === "sending"
            ? "var(--surface-high)"
            : "linear-gradient(135deg, #1D9E75, #14785a)",
          color: "#fff", fontSize: 14, fontWeight: 700,
          fontFamily: "var(--font-display)", letterSpacing: "0.3px",
          cursor: status === "sending" ? "wait" : "pointer",
          boxShadow: "0 4px 15px rgba(29, 158, 117, 0.3)",
          opacity: status === "sending" ? 0.7 : 1,
        }}>
        {status === "sending" ? "⏳ Sending Report..." : "📧 Send Candidates Report"}
      </button>

      {/* Status Message */}
      {result && (
        <div style={{
          padding: "10px 14px", borderRadius: 6, fontSize: 12, fontWeight: 500,
          background: status === "sent" ? "rgba(29, 158, 117, 0.1)" : "rgba(230, 77, 77, 0.1)",
          color: status === "sent" ? "#1D9E75" : "#E64D4D",
          border: `1px solid ${status === "sent" ? "rgba(29, 158, 117, 0.2)" : "rgba(230, 77, 77, 0.2)"}`,
        }}>
          {result}
        </div>
      )}
    </div>
  )
}
