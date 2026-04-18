"use client";

import { useState } from "react";
import { FileText, AlertTriangle, Clock, CheckCircle, Send } from "lucide-react";
import { SeverityBadge } from "@/components/common/severity-badge";

const STATS = [
  { label: "Verified", value: "0", icon: FileText, cls: "bg-blue-50 text-blue-600" },
  { label: "Critical", value: "0", icon: AlertTriangle, cls: "bg-red-50 text-red-600" },
  { label: "Pending", value: "0", icon: Clock, cls: "bg-amber-50 text-amber-600" },
  { label: "Resolved", value: "0", icon: CheckCircle, cls: "bg-gray-50 text-gray-600" },
];

export default function DashboardPage() {
  const [docText, setDocText] = useState("");
  const [docType, setDocType] = useState("brief");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!docText.trim()) return;
    setSubmitting(true);
    setTimeout(() => setSubmitting(false), 1500);
  };

  const textSizeKb = new TextEncoder().encode(docText).length / 1024;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          AI verification overview for your firm.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {STATS.map((stat) => (
          <div key={stat.label} className="card-hover flex items-center gap-3 p-4">
            <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${stat.cls}`}>
              <stat.icon className="h-4 w-4" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              <p className="text-xs text-gray-500">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Paste & Test */}
      <div className="card">
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3">
          <h2 className="text-sm font-medium text-gray-900">Paste & Test</h2>
          <span className="badge border border-indigo-200 bg-indigo-50 text-indigo-600 text-[10px]">SDK also available</span>
        </div>
        <div className="p-5">
          <textarea
            value={docText}
            onChange={(e) => setDocText(e.target.value)}
            className="input min-h-[200px] resize-y font-mono text-sm"
            placeholder={`Paste AI-generated legal text here...\n\nExample:\nIn Smith v. Jones, 123 F.3d 456 (9th Cir. 2019),\nthe court held that "the moving party bears the\ninitial burden of demonstrating the absence of a\ngenuine issue of material fact."`}
          />
          <div className="mt-3 flex items-center justify-between">
            <div className="text-xs text-gray-400">
              {docText.length > 0 && (
                <span className={textSizeKb > 200 ? "font-medium text-severity-critical" : ""}>
                  {textSizeKb.toFixed(1)} KB / 200 KB
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <select value={docType} onChange={(e) => setDocType(e.target.value)} className="select w-28 py-1.5 text-xs">
                <option value="brief">Brief</option>
                <option value="memo">Memo</option>
                <option value="contract">Contract</option>
                <option value="other">Other</option>
              </select>
              <button onClick={handleSubmit} disabled={!docText.trim() || submitting || textSizeKb > 200} className="btn-primary text-sm">
                <Send className="h-3.5 w-3.5" />
                {submitting ? "Verifying..." : "Verify"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Severity */}
      <div className="card p-5">
        <h3 className="text-xs font-medium uppercase tracking-wide text-gray-400">Severity Levels</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          <SeverityBadge severity="CRITICAL" />
          <SeverityBadge severity="HIGH" />
          <SeverityBadge severity="MEDIUM" />
          <SeverityBadge severity="ADVISORY" />
        </div>
        <p className="mt-2 text-[11px] text-gray-400">Color + icon + text. Never color alone. Never green.</p>
      </div>

      {/* Activity */}
      <div className="card">
        <div className="border-b border-gray-200 px-5 py-3">
          <h2 className="text-sm font-medium text-gray-900">Recent Activity</h2>
        </div>
        <div className="p-8 text-center">
          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-gray-100">
            <FileText className="h-5 w-5 text-gray-400" />
          </div>
          <p className="text-sm text-gray-500">No activity yet. Submit your first document above.</p>
        </div>
      </div>
    </div>
  );
}
