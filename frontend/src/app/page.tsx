"use client";
import { useState, useCallback } from "react";

// ── Types ──────────────────────────────────────────────────────────────────────
type Mode = "tabular" | "relational" | "document";
type DocType = "invoice" | "bank_statement" | "receipt";

interface Column {
  id: string;
  name: string;
  type: string;
  min?: number;
  max?: number;
  is_primary_key: boolean;
  categories?: string;
}

const COLUMN_TYPES = [
  { value: "string",      label: "String",      icon: "T" },
  { value: "integer",     label: "Integer",      icon: "#" },
  { value: "float",       label: "Float",        icon: ".1" },
  { value: "boolean",     label: "Boolean",      icon: "⊤" },
  { value: "datetime",    label: "DateTime",     icon: "📅" },
  { value: "uuid",        label: "UUID",         icon: "🔑" },
  { value: "name",        label: "Full Name",    icon: "👤" },
  { value: "email",       label: "Email",        icon: "✉" },
  { value: "phone",       label: "Phone",        icon: "📞" },
  { value: "address",     label: "Address",      icon: "📍" },
  { value: "company",     label: "Company",      icon: "🏢" },
  { value: "product",     label: "Product",      icon: "📦" },
  { value: "status",      label: "Status",       icon: "🔴" },
  { value: "categorical", label: "Categorical",  icon: "≡" },
];

const API = process.env.NEXT_PUBLIC_API_URL || "";

// ── Helpers ────────────────────────────────────────────────────────────────────
const uid = () => Math.random().toString(36).slice(2, 8);

function typeColor(type: string) {
  const map: Record<string, string> = {
    integer: "#3b82f6", float: "#8b5cf6", boolean: "#10b981",
    datetime: "#f59e0b", uuid: "#06b6d4", name: "#ec4899",
    email: "#f97316", phone: "#14b8a6", address: "#84cc16",
    company: "#a855f7", product: "#ef4444", status: "#fb923c",
    categorical: "#6366f1", string: "#94a3b8",
  };
  return map[type] || "#94a3b8";
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function Home() {
  const [mode, setMode] = useState<Mode>("tabular");
  const [columns, setColumns] = useState<Column[]>([
    { id: uid(), name: "id",         type: "integer", min: 1, max: 9999, is_primary_key: true },
    { id: uid(), name: "full_name",  type: "name",    is_primary_key: false },
    { id: uid(), name: "email",      type: "email",   is_primary_key: false },
    { id: uid(), name: "created_at", type: "datetime", is_primary_key: false },
    { id: uid(), name: "balance",    type: "float", min: 0, max: 5000, is_primary_key: false },
  ]);
  const [rowCount, setRowCount] = useState(50);
  const [nullRate, setNullRate] = useState(0.05);
  const [outlierRate, setOutlierRate] = useState(0.02);
  const [seed, setSeed] = useState(42);
  const [docType, setDocType] = useState<DocType>("invoice");
  const [docCount, setDocCount] = useState(5);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"table" | "json" | "validation">("table");

  // ── Column helpers ──────────────────────────────────────────────────────────
  const addColumn = () =>
    setColumns(prev => [...prev, { id: uid(), name: `col_${prev.length + 1}`, type: "string", is_primary_key: false }]);

  const removeColumn = (id: string) =>
    setColumns(prev => prev.filter(c => c.id !== id));

  const updateColumn = (id: string, key: keyof Column, value: any) =>
    setColumns(prev => prev.map(c => c.id === id ? { ...c, [key]: value } : c));

  // ── Generate ────────────────────────────────────────────────────────────────
  const generate = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      if (mode === "tabular") {
        const body = {
          table_name: "dataset",
          columns: columns.map(c => ({
            name: c.name,
            type: c.type,
            is_primary_key: c.is_primary_key,
            ...(c.min !== undefined ? { min: c.min } : {}),
            ...(c.max !== undefined ? { max: c.max } : {}),
            ...(c.categories ? { categories: c.categories.split(",").map(s => s.trim()) } : {}),
          })),
          config: { row_count: rowCount, seed, null_rate: nullRate, outlier_rate: outlierRate },
        };
        const res = await fetch(`${API}/api/generate/tabular`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(await res.text());
        setResult(await res.json());
        setActiveTab("table");
      } else if (mode === "relational") {
        const res = await fetch(`${API}/api/generate/relational/preset/ecommerce`, { method: "POST" });
        if (!res.ok) throw new Error(await res.text());
        setResult(await res.json());
        setActiveTab("json");
      } else {
        const res = await fetch(`${API}/api/generate/document`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ doc_type: docType, count: docCount, seed }),
        });
        if (!res.ok) throw new Error(await res.text());
        setResult(await res.json());
        setActiveTab("json");
      }
    } catch (e: any) {
      setError(e.message || "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  }, [mode, columns, rowCount, seed, nullRate, outlierRate, docType, docCount]);

  // ── Export ──────────────────────────────────────────────────────────────────
  const exportData = async (fmt: "csv" | "json") => {
    if (!result) return;
    const data = result.preview || result.documents || [];
    if (!data.length) return;
    try {
      const res = await fetch(`${API}/api/export/${fmt}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data, format: fmt, filename: `synthetic_${mode}` }),
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `synthetic_${mode}.${fmt}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch { /* silent */ }
  };

  // ── Render helpers ──────────────────────────────────────────────────────────
  const previewRows: any[] = result?.preview || [];
  const previewCols: string[] = previewRows.length > 0 ? Object.keys(previewRows[0]) : [];
  const validation = result?.validation || null;

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden", background: "var(--bg-primary)", fontFamily: "'Inter', sans-serif" }}>

      {/* ── LEFT SIDEBAR ──────────────────────────────────────────────────── */}
      <aside style={{ width: 240, background: "var(--bg-secondary)", borderRight: "1px solid var(--border)", display: "flex", flexDirection: "column", flexShrink: 0 }}>
        {/* Logo */}
        <div style={{ padding: "20px 20px 16px", borderBottom: "1px solid var(--border)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 34, height: 34, borderRadius: 8, background: "linear-gradient(135deg, #3b82f6, #8b5cf6)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16 }}>⚡</div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 15, color: "var(--text-primary)", letterSpacing: "-0.3px" }}>SynthLab</div>
              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Data Platform</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav style={{ padding: "12px 10px", flex: 1 }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase", padding: "0 10px 8px" }}>Generate</div>
          {(["tabular", "relational", "document"] as Mode[]).map(m => {
            const icons: Record<Mode, string> = { tabular: "⊞", relational: "🔗", document: "📄" };
            const labels: Record<Mode, string> = { tabular: "Tabular", relational: "Relational", document: "Documents" };
            const active = mode === m;
            return (
              <button key={m} id={`mode-${m}`} onClick={() => { setMode(m); setResult(null); }}
                style={{
                  width: "100%", display: "flex", alignItems: "center", gap: 10, padding: "9px 12px",
                  borderRadius: 8, border: "none", cursor: "pointer", marginBottom: 2, textAlign: "left",
                  background: active ? "rgba(59,130,246,0.15)" : "transparent",
                  color: active ? "var(--accent-blue)" : "var(--text-secondary)",
                  fontWeight: active ? 600 : 400, fontSize: 14, transition: "all 0.15s",
                }}>
                <span style={{ fontSize: 16 }}>{icons[m]}</span>{labels[m]}
              </button>
            );
          })}

          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase", padding: "16px 10px 8px" }}>Presets</div>
          {["E-Commerce", "Healthcare", "Finance"].map(p => (
            <button key={p} style={{
              width: "100%", display: "flex", alignItems: "center", gap: 10, padding: "8px 12px",
              borderRadius: 8, border: "none", cursor: "pointer", marginBottom: 2,
              background: "transparent", color: "var(--text-muted)", fontSize: 13,
            }}
              onClick={() => { if (p === "E-Commerce") { setMode("relational"); setResult(null); } }}
            >
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--border)", display: "inline-block" }} />
              {p}
            </button>
          ))}
        </nav>

        {/* Status */}
        <div style={{ padding: "12px 16px", borderTop: "1px solid var(--border)", fontSize: 11, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--accent-green)", display: "inline-block", boxShadow: "0 0 6px #10b981" }} />
          API Ready
        </div>
      </aside>

      {/* ── MAIN AREA ─────────────────────────────────────────────────────── */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

        {/* Top Bar */}
        <header style={{ height: 56, background: "var(--bg-secondary)", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 24px", flexShrink: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Workspace</span>
            <span style={{ color: "var(--border)" }}>/</span>
            <span style={{ fontSize: 13, color: "var(--text-primary)", fontWeight: 500, textTransform: "capitalize" }}>{mode}</span>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            {result && (
              <>
                <button onClick={() => exportData("csv")} id="export-csv"
                  style={{ padding: "7px 14px", background: "transparent", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text-secondary)", fontSize: 12, cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}>
                  ⬇ CSV
                </button>
                <button onClick={() => exportData("json")} id="export-json"
                  style={{ padding: "7px 14px", background: "transparent", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text-secondary)", fontSize: 12, cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}>
                  ⬇ JSON
                </button>
              </>
            )}
            <button onClick={generate} id="generate-btn" disabled={loading}
              style={{
                padding: "8px 20px", background: loading ? "#2a3554" : "linear-gradient(135deg, #3b82f6, #8b5cf6)",
                border: "none", borderRadius: 8, color: "#fff", fontSize: 13, fontWeight: 600, cursor: loading ? "not-allowed" : "pointer",
                display: "flex", alignItems: "center", gap: 8, transition: "opacity 0.2s",
                opacity: loading ? 0.7 : 1,
              }}>
              {loading ? (
                <><span style={{ animation: "spin 1s linear infinite", display: "inline-block" }}>⟳</span> Generating…</>
              ) : "⚡ Generate"}
            </button>
          </div>
        </header>

        {/* Body: Config + Preview */}
        <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>

          {/* ── CONFIG PANEL ──────────────────────────────────────────────── */}
          <div style={{ width: 340, background: "var(--bg-card)", borderRight: "1px solid var(--border)", overflowY: "auto", flexShrink: 0 }}>
            <div style={{ padding: 20 }}>

              {/* Global settings */}
              <Section title="Settings">
                <Label>Row Count</Label>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                  <input type="range" min={10} max={10000} value={rowCount} onChange={e => setRowCount(+e.target.value)}
                    style={{ flex: 1, accentColor: "var(--accent-blue)" }} />
                  <NumInput value={rowCount} onChange={setRowCount} min={1} max={100000} />
                </div>
                <Label>Null Rate</Label>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                  <input type="range" min={0} max={0.5} step={0.01} value={nullRate} onChange={e => setNullRate(+e.target.value)}
                    style={{ flex: 1, accentColor: "var(--accent-violet)" }} />
                  <span style={{ color: "var(--text-secondary)", fontSize: 12, width: 36 }}>{(nullRate * 100).toFixed(0)}%</span>
                </div>
                <Label>Outlier Rate</Label>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                  <input type="range" min={0} max={0.2} step={0.01} value={outlierRate} onChange={e => setOutlierRate(+e.target.value)}
                    style={{ flex: 1, accentColor: "var(--accent-orange)" }} />
                  <span style={{ color: "var(--text-secondary)", fontSize: 12, width: 36 }}>{(outlierRate * 100).toFixed(0)}%</span>
                </div>
                <Label>Random Seed</Label>
                <NumInput value={seed} onChange={setSeed} min={0} max={99999} fullWidth />
              </Section>

              {/* Mode-specific */}
              {mode === "tabular" && (
                <Section title="Schema Columns">
                  {columns.map((col, idx) => (
                    <ColumnRow key={col.id} col={col} idx={idx} onUpdate={updateColumn} onRemove={removeColumn} />
                  ))}
                  <button onClick={addColumn} id="add-col-btn"
                    style={{ width: "100%", marginTop: 8, padding: "8px", background: "rgba(59,130,246,0.08)", border: "1px dashed var(--accent-blue)", borderRadius: 8, color: "var(--accent-blue)", fontSize: 13, cursor: "pointer" }}>
                    + Add Column
                  </button>
                </Section>
              )}

              {mode === "relational" && (
                <Section title="Preset Tables">
                  <InfoCard icon="🏪" title="Customers" desc="50 rows · id, name, email, city, status" />
                  <InfoCard icon="📦" title="Orders" desc="150 rows · FK → customers.id" />
                  <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>FK integrity is validated automatically.</p>
                </Section>
              )}

              {mode === "document" && (
                <Section title="Document Settings">
                  <Label>Document Type</Label>
                  <select value={docType} onChange={e => setDocType(e.target.value as DocType)} id="doc-type"
                    style={{ width: "100%", padding: "8px 12px", background: "var(--bg-input)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text-primary)", fontSize: 13, marginBottom: 12 }}>
                    <option value="invoice">Invoice</option>
                    <option value="bank_statement">Bank Statement</option>
                    <option value="receipt">Receipt</option>
                  </select>
                  <Label>Document Count</Label>
                  <NumInput value={docCount} onChange={setDocCount} min={1} max={100} fullWidth />
                </Section>
              )}
            </div>
          </div>

          {/* ── PREVIEW AREA ──────────────────────────────────────────────── */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
            {/* Tabs */}
            <div style={{ display: "flex", gap: 0, borderBottom: "1px solid var(--border)", background: "var(--bg-secondary)", padding: "0 24px", flexShrink: 0 }}>
              {(["table", "json", "validation"] as const).map(tab => (
                <button key={tab} onClick={() => setActiveTab(tab)}
                  style={{
                    padding: "14px 18px", background: "none", border: "none", cursor: "pointer", fontSize: 13, fontWeight: 500,
                    color: activeTab === tab ? "var(--accent-blue)" : "var(--text-muted)",
                    borderBottom: activeTab === tab ? "2px solid var(--accent-blue)" : "2px solid transparent",
                    textTransform: "capitalize", transition: "color 0.15s",
                  }}>
                  {tab === "table" ? "⊞ Table" : tab === "json" ? "{ } JSON" : "✓ Validation"}
                </button>
              ))}
              {result && (
                <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 16, paddingRight: 8 }}>
                  {result.total_rows && <Chip label={`${result.total_rows} rows`} color="var(--accent-blue)" />}
                  {result.metadata?.generation_time_s && <Chip label={`${result.metadata.generation_time_s}s`} color="var(--accent-green)" />}
                </div>
              )}
            </div>

            {/* Content */}
            <div style={{ flex: 1, overflow: "auto", padding: 24 }}>
              {error && (
                <div style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 10, padding: "14px 18px", color: "#fca5a5", fontSize: 13, marginBottom: 16 }}>
                  ⚠ {error}
                </div>
              )}

              {!result && !loading && !error && (
                <EmptyState mode={mode} />
              )}

              {loading && <LoadingSpinner />}

              {result && !loading && (
                <>
                  {activeTab === "table" && mode === "tabular" && previewRows.length > 0 && (
                    <DataTable rows={previewRows} cols={previewCols} />
                  )}
                  {activeTab === "table" && mode !== "tabular" && (
                    <div style={{ color: "var(--text-secondary)", fontSize: 13 }}>
                      Switch to JSON tab to view {mode} results.
                    </div>
                  )}
                  {activeTab === "json" && (
                    <pre style={{
                      background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 12,
                      padding: 20, fontSize: 12, lineHeight: 1.7, color: "#a5f3fc",
                      fontFamily: "'JetBrains Mono', monospace", overflow: "auto", maxHeight: "70vh",
                    }}>
                      {JSON.stringify(result, null, 2)}
                    </pre>
                  )}
                  {activeTab === "validation" && validation && (
                    <ValidationPanel v={validation} />
                  )}
                  {activeTab === "validation" && !validation && (
                    <div style={{ color: "var(--text-muted)", fontSize: 13 }}>No validation data available for this mode.</div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </main>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}

// ── Small Components ───────────────────────────────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <h3 style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 12 }}>{title}</h3>
      {children}
    </div>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4, fontWeight: 500 }}>{children}</div>;
}

function NumInput({ value, onChange, min, max, fullWidth }: { value: number; onChange: (v: number) => void; min?: number; max?: number; fullWidth?: boolean }) {
  return (
    <input type="number" value={value} min={min} max={max}
      onChange={e => onChange(+e.target.value)}
      style={{ width: fullWidth ? "100%" : 60, padding: "6px 8px", background: "var(--bg-input)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-primary)", fontSize: 12, textAlign: "center", marginBottom: fullWidth ? 12 : 0 }} />
  );
}

function InfoCard({ icon, title, desc }: { icon: string; title: string; desc: string }) {
  return (
    <div style={{ background: "var(--bg-input)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 12px", marginBottom: 8, display: "flex", gap: 10, alignItems: "flex-start" }}>
      <span style={{ fontSize: 18 }}>{icon}</span>
      <div>
        <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text-primary)" }}>{title}</div>
        <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>{desc}</div>
      </div>
    </div>
  );
}

function Chip({ label, color }: { label: string; color: string }) {
  return (
    <span style={{ fontSize: 11, padding: "3px 8px", borderRadius: 20, background: `${color}22`, color, border: `1px solid ${color}44`, fontWeight: 500 }}>
      {label}
    </span>
  );
}

function ColumnRow({ col, idx, onUpdate, onRemove }: { col: Column; idx: number; onUpdate: (id: string, k: keyof Column, v: any) => void; onRemove: (id: string) => void }) {
  const color = typeColor(col.type);
  return (
    <div style={{ background: "var(--bg-input)", border: "1px solid var(--border)", borderRadius: 10, padding: 12, marginBottom: 8, animation: "fadeIn 0.2s ease" }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <input value={col.name} onChange={e => onUpdate(col.id, "name", e.target.value)}
          placeholder="column_name"
          style={{ flex: 1, padding: "6px 10px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-primary)", fontSize: 12 }} />
        <button onClick={() => onRemove(col.id)}
          style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 6, color: "#f87171", padding: "6px 10px", cursor: "pointer", fontSize: 12 }}>✕</button>
      </div>
      <select value={col.type} onChange={e => onUpdate(col.id, "type", e.target.value)}
        style={{ width: "100%", padding: "6px 10px", background: "var(--bg-card)", border: `1px solid ${color}55`, borderRadius: 6, color, fontSize: 12, marginBottom: 6 }}>
        {COLUMN_TYPES.map(t => <option key={t.value} value={t.value}>{t.icon} {t.label}</option>)}
      </select>
      {(col.type === "integer" || col.type === "float") && (
        <div style={{ display: "flex", gap: 6 }}>
          <input type="number" placeholder="min" value={col.min ?? ""} onChange={e => onUpdate(col.id, "min", +e.target.value)}
            style={{ flex: 1, padding: "5px 8px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-primary)", fontSize: 11 }} />
          <input type="number" placeholder="max" value={col.max ?? ""} onChange={e => onUpdate(col.id, "max", +e.target.value)}
            style={{ flex: 1, padding: "5px 8px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-primary)", fontSize: 11 }} />
        </div>
      )}
      {col.type === "categorical" && (
        <input placeholder="A, B, C" value={col.categories || ""} onChange={e => onUpdate(col.id, "categories", e.target.value)}
          style={{ width: "100%", padding: "5px 8px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-primary)", fontSize: 11, marginTop: 4 }} />
      )}
      <label style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 8, fontSize: 11, color: "var(--text-muted)", cursor: "pointer" }}>
        <input type="checkbox" checked={col.is_primary_key} onChange={e => onUpdate(col.id, "is_primary_key", e.target.checked)}
          style={{ accentColor: "var(--accent-blue)" }} />
        Primary Key
      </label>
    </div>
  );
}

function DataTable({ rows, cols }: { rows: any[]; cols: string[] }) {
  return (
    <div style={{ borderRadius: 12, border: "1px solid var(--border)", overflow: "hidden", animation: "fadeIn 0.3s ease" }}>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, fontFamily: "'JetBrains Mono', monospace" }}>
          <thead>
            <tr style={{ background: "var(--bg-card)" }}>
              <th style={{ padding: "10px 14px", textAlign: "right", color: "var(--text-muted)", borderBottom: "1px solid var(--border)", fontFamily: "Inter", fontSize: 11, fontWeight: 500, width: 48 }}>#</th>
              {cols.map(col => (
                <th key={col} style={{ padding: "10px 14px", textAlign: "left", color: "var(--text-secondary)", borderBottom: "1px solid var(--border)", fontFamily: "Inter", fontSize: 11, fontWeight: 500, whiteSpace: "nowrap" }}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 200).map((row, i) => (
              <tr key={i} style={{ background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.015)", transition: "background 0.1s" }}
                onMouseEnter={e => (e.currentTarget.style.background = "rgba(59,130,246,0.06)")}
                onMouseLeave={e => (e.currentTarget.style.background = i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.015)")}>
                <td style={{ padding: "8px 14px", color: "var(--text-muted)", borderBottom: "1px solid rgba(42,53,84,0.5)", textAlign: "right", fontSize: 11 }}>{i + 1}</td>
                {cols.map(col => {
                  const v = row[col];
                  const isNull = v === null || v === undefined;
                  return (
                    <td key={col} style={{ padding: "8px 14px", color: isNull ? "var(--text-muted)" : "var(--text-primary)", borderBottom: "1px solid rgba(42,53,84,0.5)", whiteSpace: "nowrap", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis" }}>
                      {isNull ? <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>null</span> : String(v)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > 200 && (
        <div style={{ padding: "10px 16px", background: "var(--bg-card)", borderTop: "1px solid var(--border)", fontSize: 11, color: "var(--text-muted)", textAlign: "center" }}>
          Showing 200 of {rows.length} rows — export to see all data
        </div>
      )}
    </div>
  );
}

function ValidationPanel({ v }: { v: any }) {
  const pass = v.status === "PASS";
  return (
    <div style={{ animation: "fadeIn 0.3s ease" }}>
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <MetricCard label="Status" value={v.status} color={pass ? "var(--accent-green)" : "var(--accent-orange)"} />
        <MetricCard label="Rows" value={v.row_count ?? "—"} color="var(--accent-blue)" />
        <MetricCard label="Columns" value={v.column_count ?? "—"} color="var(--accent-violet)" />
        <MetricCard label="Null Rate" value={v.null_rate_overall !== undefined ? `${(v.null_rate_overall * 100).toFixed(1)}%` : "—"} color="var(--accent-orange)" />
        <MetricCard label="PK Unique" value={v.pk_unique !== undefined ? (v.pk_unique ? "✓" : "✗") : "—"} color={v.pk_unique ? "var(--accent-green)" : "var(--accent-orange)"} />
      </div>
      {v.issues && v.issues.length > 0 && (
        <div style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.25)", borderRadius: 10, padding: 14, marginBottom: 16 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#fbbf24", marginBottom: 8 }}>⚠ Issues</div>
          {v.issues.map((issue: string, i: number) => (
            <div key={i} style={{ fontSize: 12, color: "#fcd34d", marginBottom: 4 }}>• {issue}</div>
          ))}
        </div>
      )}
      {v.null_rates_per_column && (
        <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 10, padding: 14 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.06em" }}>Null Rate per Column</div>
          {Object.entries(v.null_rates_per_column).map(([col, rate]: [string, any]) => (
            <div key={col} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <span style={{ width: 120, fontSize: 12, color: "var(--text-secondary)", fontFamily: "JetBrains Mono", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{col}</span>
              <div style={{ flex: 1, height: 6, background: "var(--bg-input)", borderRadius: 3, overflow: "hidden" }}>
                <div style={{ width: `${(rate as number) * 100}%`, height: "100%", background: rate > 0.1 ? "var(--accent-orange)" : "var(--accent-blue)", borderRadius: 3, transition: "width 0.5s ease" }} />
              </div>
              <span style={{ fontSize: 11, color: "var(--text-muted)", width: 38, textAlign: "right" }}>{((rate as number) * 100).toFixed(1)}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, color }: { label: string; value: any; color: string }) {
  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 10, padding: "12px 18px", minWidth: 100 }}>
      <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700, color }}>{value}</div>
    </div>
  );
}

function EmptyState({ mode }: { mode: Mode }) {
  const msgs: Record<Mode, { icon: string; title: string; desc: string }> = {
    tabular:    { icon: "⊞", title: "Configure your schema", desc: "Define columns on the left, then hit Generate to create synthetic tabular data." },
    relational: { icon: "🔗", title: "E-Commerce dataset ready", desc: "Click Generate to create a linked Customers + Orders dataset with FK integrity." },
    document:   { icon: "📄", title: "Document generator", desc: "Select a document type and count, then Generate to produce realistic invoices or bank statements." },
  };
  const m = msgs[mode];
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 16, opacity: 0.6 }}>
      <div style={{ fontSize: 64 }}>{m.icon}</div>
      <div style={{ fontSize: 18, fontWeight: 600, color: "var(--text-secondary)" }}>{m.title}</div>
      <div style={{ fontSize: 13, color: "var(--text-muted)", textAlign: "center", maxWidth: 360 }}>{m.desc}</div>
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "60%", gap: 16 }}>
      <div style={{
        width: 48, height: 48, border: "3px solid var(--border)", borderTopColor: "var(--accent-blue)",
        borderRadius: "50%", animation: "spin 0.8s linear infinite",
      }} />
      <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Generating synthetic data…</div>
    </div>
  );
}
