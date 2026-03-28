"use client";

import { useState, useRef, useEffect } from "react";
import { Shield, Terminal, AlertTriangle, Send, Loader2, ChevronDown, Cpu, FileSearch } from "lucide-react";

type Mode = "explain" | "attacker" | "defender";
type Tab = "chat" | "analyze";
type Severity = "critical" | "high" | "medium" | "low" | "info";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  timestamp: Date;
}

interface Threat {
  threat_type: string;
  severity: Severity;
  confidence: number;
  description: string;
  attacker_perspective: string;
  defender_perspective: string;
  mitigation_steps: string[];
  real_world_commands: string[];
  cve_references: string[];
  owasp_category: string;
}

interface AnalyzeResult {
  input_type: string;
  threats: Threat[];
  overall_severity: Severity;
  summary: string;
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const SEVERITY_CONFIG: Record<Severity, { label: string; color: string; bg: string; border: string }> = {
  critical: { label: "CRITICAL", color: "#ff2d55", bg: "rgba(255,45,85,0.12)", border: "rgba(255,45,85,0.4)" },
  high:     { label: "HIGH",     color: "#ff6b00", bg: "rgba(255,107,0,0.12)", border: "rgba(255,107,0,0.4)" },
  medium:   { label: "MEDIUM",   color: "#ffd60a", bg: "rgba(255,214,10,0.10)", border: "rgba(255,214,10,0.4)" },
  low:      { label: "LOW",      color: "#30d158", bg: "rgba(48,209,88,0.10)", border: "rgba(48,209,88,0.4)" },
  info:     { label: "INFO",     color: "#636366", bg: "rgba(99,99,102,0.10)", border: "rgba(99,99,102,0.3)" },
};

export default function Home() {
  const [tab, setTab] = useState<Tab>("chat");
  const [mode, setMode] = useState<Mode>("explain");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "**CyberSec Copilot online.**\n\nI'm your AI-powered security analyst. Ask me about vulnerabilities, attack vectors, CVEs, or paste logs/code for threat analysis.\n\nSwitch tabs to use **Analyze** mode for structured log and code scanning.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [analyzeInput, setAnalyzeInput] = useState("");
  const [analyzeType, setAnalyzeType] = useState<"auto" | "log" | "code">("auto");
  const [isLoading, setIsLoading] = useState(false);
  const [analyzeResult, setAnalyzeResult] = useState<AnalyzeResult | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendChat() {
    if (!input.trim() || isLoading) return;
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg.content, mode }),
      });
      const data = await res.json();
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response || data.detail || "No response received.",
        sources: data.sources,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "⚠️ Connection error. Is the backend running at " + API + "?",
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
    }
  }

  async function runAnalysis() {
    if (!analyzeInput.trim() || isLoading) return;
    setIsLoading(true);
    setAnalyzeResult(null);
    try {
      const res = await fetch(`${API}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: analyzeInput, type: analyzeType }),
      });
      const data = await res.json();
      setAnalyzeResult(data);
    } catch {
      setAnalyzeResult(null);
    } finally {
      setIsLoading(false);
    }
  }

  function renderMessageContent(content: string) {
    const lines = content.split("\n");
    return lines.map((line, i) => {
      const boldReplaced = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      return (
        <span key={i}>
          <span dangerouslySetInnerHTML={{ __html: boldReplaced }} />
          {i < lines.length - 1 && <br />}
        </span>
      );
    });
  }

  const sev = analyzeResult ? SEVERITY_CONFIG[analyzeResult.overall_severity] : null;

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0a0a0f",
      color: "#e8e8f0",
      fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
      display: "flex",
      flexDirection: "column",
    }}>
      {/* Header */}
      <header style={{
        borderBottom: "1px solid rgba(0,255,136,0.15)",
        padding: "16px 28px",
        display: "flex",
        alignItems: "center",
        gap: "12px",
        background: "rgba(0,255,136,0.02)",
        backdropFilter: "blur(10px)",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}>
        <div style={{
          width: 36, height: 36,
          borderRadius: 8,
          background: "linear-gradient(135deg, #00ff88 0%, #00b4d8 100%)",
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 0 20px rgba(0,255,136,0.3)",
        }}>
          <Shield size={20} color="#0a0a0f" />
        </div>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: "0.05em", color: "#00ff88" }}>
            CYBERSEC COPILOT
          </div>
          <div style={{ fontSize: 10, color: "#636366", letterSpacing: "0.12em" }}>
            AI-POWERED SECURITY ANALYST
          </div>
        </div>

        {/* Status dot */}
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 8, height: 8, borderRadius: "50%",
            background: "#00ff88",
            boxShadow: "0 0 8px #00ff88",
            animation: "pulse 2s infinite",
          }} />
          <span style={{ fontSize: 11, color: "#636366", letterSpacing: "0.08em" }}>ONLINE</span>
        </div>
      </header>

      {/* Tab Bar */}
      <div style={{
        display: "flex",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        padding: "0 28px",
        background: "rgba(255,255,255,0.01)",
      }}>
        {([["chat", "Chat", <Cpu size={14} />], ["analyze", "Analyze", <FileSearch size={14} />]] as const).map(([t, label, icon]) => (
          <button
            key={t}
            onClick={() => setTab(t as Tab)}
            style={{
              display: "flex", alignItems: "center", gap: 7,
              padding: "12px 20px",
              background: "none", border: "none", cursor: "pointer",
              fontSize: 12, letterSpacing: "0.08em", fontFamily: "inherit",
              color: tab === t ? "#00ff88" : "#636366",
              borderBottom: tab === t ? "2px solid #00ff88" : "2px solid transparent",
              transition: "all 0.2s",
              marginBottom: -1,
            }}
          >
            {icon}
            {label.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Main */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", maxWidth: 1000, margin: "0 auto", width: "100%", padding: "0 16px" }}>

        {/* ─── CHAT TAB ─── */}
        {tab === "chat" && (
          <>
            {/* Mode selector */}
            <div style={{ padding: "16px 0 0", display: "flex", gap: 8 }}>
              {(["explain", "attacker", "defender"] as Mode[]).map(m => (
                <button key={m} onClick={() => setMode(m)} style={{
                  padding: "6px 14px",
                  borderRadius: 20,
                  border: `1px solid ${mode === m ? "#00ff88" : "rgba(255,255,255,0.08)"}`,
                  background: mode === m ? "rgba(0,255,136,0.1)" : "transparent",
                  color: mode === m ? "#00ff88" : "#636366",
                  fontSize: 11, letterSpacing: "0.08em",
                  cursor: "pointer", fontFamily: "inherit",
                  transition: "all 0.2s",
                }}>
                  {m === "explain" ? "🔍" : m === "attacker" ? "💀" : "🛡️"} {m.toUpperCase()}
                </button>
              ))}
            </div>

            {/* Messages */}
            <div style={{
              flex: 1, overflowY: "auto", padding: "20px 0",
              display: "flex", flexDirection: "column", gap: 16,
              minHeight: 400, maxHeight: "calc(100vh - 300px)",
            }}>
              {messages.map(msg => (
                <div key={msg.id} style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: msg.role === "user" ? "flex-end" : "flex-start",
                }}>
                  <div style={{
                    maxWidth: "82%",
                    padding: "14px 18px",
                    borderRadius: msg.role === "user" ? "16px 16px 4px 16px" : "4px 16px 16px 16px",
                    background: msg.role === "user"
                      ? "linear-gradient(135deg, rgba(0,255,136,0.15) 0%, rgba(0,180,216,0.15) 100%)"
                      : "rgba(255,255,255,0.04)",
                    border: msg.role === "user"
                      ? "1px solid rgba(0,255,136,0.2)"
                      : "1px solid rgba(255,255,255,0.06)",
                    fontSize: 13, lineHeight: 1.7,
                  }}>
                    {msg.role === "assistant" && (
                      <div style={{ fontSize: 10, color: "#00ff88", letterSpacing: "0.1em", marginBottom: 8 }}>
                        ◈ COPILOT
                      </div>
                    )}
                    {renderMessageContent(msg.content)}
                    {msg.sources && msg.sources.length > 0 && (
                      <div style={{ marginTop: 10, paddingTop: 8, borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                        <div style={{ fontSize: 10, color: "#636366", letterSpacing: "0.08em" }}>SOURCES</div>
                        {msg.sources.map((s, i) => (
                          <div key={i} style={{ fontSize: 11, color: "#00b4d8", marginTop: 3 }}>↗ {s}</div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div style={{ display: "flex", alignItems: "center", gap: 10, color: "#636366" }}>
                  <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} />
                  <span style={{ fontSize: 12 }}>Analysing…</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input */}
            <div style={{
              padding: "16px 0 24px",
              display: "flex", gap: 10,
              borderTop: "1px solid rgba(255,255,255,0.06)",
            }}>
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && !e.shiftKey && sendChat()}
                placeholder="Ask about CVEs, attack techniques, defence strategies…"
                style={{
                  flex: 1, padding: "12px 16px",
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: 10, color: "#e8e8f0",
                  fontSize: 13, fontFamily: "inherit",
                  outline: "none",
                }}
              />
              <button
                onClick={sendChat}
                disabled={isLoading || !input.trim()}
                style={{
                  padding: "12px 20px",
                  background: "linear-gradient(135deg, #00ff88, #00b4d8)",
                  border: "none", borderRadius: 10,
                  cursor: "pointer", display: "flex", alignItems: "center", gap: 8,
                  fontSize: 12, fontWeight: 700, color: "#0a0a0f",
                  fontFamily: "inherit", letterSpacing: "0.06em",
                  opacity: isLoading || !input.trim() ? 0.5 : 1,
                  transition: "opacity 0.2s",
                }}
              >
                <Send size={14} />
                SEND
              </button>
            </div>
          </>
        )}

        {/* ─── ANALYZE TAB ─── */}
        {tab === "analyze" && (
          <div style={{ padding: "20px 0 24px", display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "flex", gap: 8 }}>
              {(["auto", "log", "code"] as const).map(t => (
                <button key={t} onClick={() => setAnalyzeType(t)} style={{
                  padding: "6px 14px", borderRadius: 20,
                  border: `1px solid ${analyzeType === t ? "#00b4d8" : "rgba(255,255,255,0.08)"}`,
                  background: analyzeType === t ? "rgba(0,180,216,0.12)" : "transparent",
                  color: analyzeType === t ? "#00b4d8" : "#636366",
                  fontSize: 11, letterSpacing: "0.08em",
                  cursor: "pointer", fontFamily: "inherit",
                }}>
                  {t === "auto" ? "⚡" : t === "log" ? "📋" : "💻"} {t.toUpperCase()}
                </button>
              ))}
            </div>

            <textarea
              value={analyzeInput}
              onChange={e => setAnalyzeInput(e.target.value)}
              placeholder={"Paste log lines or source code here…\n\nExamples:\n• Apache access logs with attack patterns\n• Python/JS code with potential vulnerabilities\n• CVE exploit payloads"}
              rows={12}
              style={{
                width: "100%", padding: "14px 16px",
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: 10, color: "#e8e8f0",
                fontSize: 12, fontFamily: "inherit",
                lineHeight: 1.6, resize: "vertical",
                outline: "none", boxSizing: "border-box",
              }}
            />

            <button
              onClick={runAnalysis}
              disabled={isLoading || !analyzeInput.trim()}
              style={{
                padding: "13px 24px",
                background: "linear-gradient(135deg, #ff6b00, #ff2d55)",
                border: "none", borderRadius: 10,
                cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
                fontSize: 13, fontWeight: 700, color: "#fff",
                fontFamily: "inherit", letterSpacing: "0.08em",
                opacity: isLoading || !analyzeInput.trim() ? 0.5 : 1,
                alignSelf: "flex-start",
              }}
            >
              {isLoading ? <Loader2 size={16} style={{ animation: "spin 1s linear infinite" }} /> : <AlertTriangle size={16} />}
              RUN THREAT ANALYSIS
            </button>

            {/* Results */}
            {analyzeResult && sev && (
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {/* Summary bar */}
                <div style={{
                  padding: "14px 18px",
                  background: sev.bg, border: `1px solid ${sev.border}`,
                  borderRadius: 10, display: "flex", alignItems: "center", gap: 12,
                }}>
                  <span style={{
                    padding: "3px 10px", borderRadius: 4,
                    background: sev.color, color: "#0a0a0f",
                    fontSize: 11, fontWeight: 700, letterSpacing: "0.1em",
                  }}>
                    {sev.label}
                  </span>
                  <span style={{ fontSize: 12, color: "#e8e8f0" }}>{analyzeResult.summary}</span>
                  <span style={{ marginLeft: "auto", fontSize: 11, color: "#636366", whiteSpace: "nowrap" }}>
                    {analyzeResult.input_type.toUpperCase()} · {analyzeResult.threats.length} THREAT{analyzeResult.threats.length !== 1 ? "S" : ""}
                  </span>
                </div>

                {/* Individual threats */}
                {analyzeResult.threats.map((threat, i) => {
                  const tc = SEVERITY_CONFIG[threat.severity];
                  return (
                    <div key={i} style={{
                      padding: 18,
                      background: "rgba(255,255,255,0.02)",
                      border: `1px solid ${tc.border}`,
                      borderLeft: `3px solid ${tc.color}`,
                      borderRadius: 10,
                    }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
                        <span style={{
                          padding: "2px 8px", borderRadius: 4,
                          background: tc.bg, color: tc.color,
                          fontSize: 10, fontWeight: 700, letterSpacing: "0.1em",
                          border: `1px solid ${tc.border}`,
                        }}>
                          {tc.label}
                        </span>
                        <span style={{ fontSize: 14, fontWeight: 700, color: "#e8e8f0" }}>
                          {threat.threat_type}
                        </span>
                        <span style={{ marginLeft: "auto", fontSize: 10, color: "#636366" }}>
                          CONFIDENCE: {Math.round(threat.confidence * 100)}%
                        </span>
                      </div>

                      {threat.owasp_category && (
                        <div style={{ fontSize: 11, color: "#00b4d8", marginBottom: 10 }}>
                          📋 {threat.owasp_category}
                        </div>
                      )}
                      {threat.cve_references.length > 0 && (
                        <div style={{ fontSize: 11, color: "#ff6b00", marginBottom: 10 }}>
                          🔗 {threat.cve_references.join(", ")}
                        </div>
                      )}

                      <p style={{ fontSize: 12, lineHeight: 1.7, color: "#b0b0c0", marginBottom: 12 }}>
                        {threat.description}
                      </p>

                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
                        <div style={{ padding: 12, background: "rgba(255,45,85,0.06)", borderRadius: 8 }}>
                          <div style={{ fontSize: 10, color: "#ff2d55", letterSpacing: "0.08em", marginBottom: 6 }}>💀 ATTACKER</div>
                          <p style={{ fontSize: 11, lineHeight: 1.6, color: "#b0b0c0", margin: 0 }}>{threat.attacker_perspective}</p>
                        </div>
                        <div style={{ padding: 12, background: "rgba(0,255,136,0.04)", borderRadius: 8 }}>
                          <div style={{ fontSize: 10, color: "#00ff88", letterSpacing: "0.08em", marginBottom: 6 }}>🛡️ DEFENDER</div>
                          <p style={{ fontSize: 11, lineHeight: 1.6, color: "#b0b0c0", margin: 0 }}>{threat.defender_perspective}</p>
                        </div>
                      </div>

                      {threat.mitigation_steps.length > 0 && (
                        <div style={{ marginBottom: 10 }}>
                          <div style={{ fontSize: 10, color: "#636366", letterSpacing: "0.08em", marginBottom: 6 }}>MITIGATIONS</div>
                          {threat.mitigation_steps.map((s, j) => (
                            <div key={j} style={{ fontSize: 11, color: "#b0b0c0", padding: "2px 0" }}>→ {s}</div>
                          ))}
                        </div>
                      )}

                      {threat.real_world_commands.length > 0 && (
                        <div>
                          <div style={{ fontSize: 10, color: "#636366", letterSpacing: "0.08em", marginBottom: 6 }}>COMMANDS</div>
                          {threat.real_world_commands.map((cmd, j) => (
                            <code key={j} style={{
                              display: "block",
                              padding: "6px 10px", marginBottom: 4,
                              background: "rgba(0,0,0,0.4)",
                              border: "1px solid rgba(255,255,255,0.06)",
                              borderRadius: 6,
                              fontSize: 11, color: "#00ff88",
                              fontFamily: "inherit",
                            }}>
                              $ {cmd}
                            </code>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </main>

      <style>{`
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
        input::placeholder, textarea::placeholder { color: #3a3a4a; }
      `}</style>
    </div>
  );
}
