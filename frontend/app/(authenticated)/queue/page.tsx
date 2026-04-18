"use client";

import { useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import { SeverityBadge } from "@/components/common/severity-badge";

type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "ADVISORY";
type DocStatus = "pending" | "in_review" | "resolved";

interface QueueDoc {
  id: string;
  status: DocStatus;
  documentType: string;
  submittedAt: string;
  flagCount: number;
  worstSeverity: Severity;
  summary: { critical: number; high: number; medium: number; advisory: number };
}

const MOCK_DOCS: QueueDoc[] = [
  { id: "cg_doc_001", status: "in_review", documentType: "brief", submittedAt: "2026-04-18T10:30:00Z", flagCount: 5, worstSeverity: "CRITICAL", summary: { critical: 2, high: 1, medium: 1, advisory: 1 } },
  { id: "cg_doc_002", status: "in_review", documentType: "memo", submittedAt: "2026-04-18T09:15:00Z", flagCount: 3, worstSeverity: "HIGH", summary: { critical: 0, high: 2, medium: 1, advisory: 0 } },
  { id: "cg_doc_003", status: "pending", documentType: "brief", submittedAt: "2026-04-18T08:00:00Z", flagCount: 1, worstSeverity: "MEDIUM", summary: { critical: 0, high: 0, medium: 1, advisory: 0 } },
];

const STATUS_STYLE: Record<DocStatus, { label: string; cls: string }> = {
  pending:   { label: "Pending",   cls: "bg-amber-50 text-amber-700" },
  in_review: { label: "In Review", cls: "bg-blue-50 text-blue-700" },
  resolved:  { label: "Resolved",  cls: "bg-gray-100 text-gray-600" },
};

export default function QueuePage() {
  const [statusFilter, setStatusFilter] = useState<DocStatus | "">("");
  const [severityFilter, setSeverityFilter] = useState<Severity | "">("");
  const [search, setSearch] = useState("");

  const filtered = MOCK_DOCS.filter((d) => {
    if (statusFilter && d.status !== statusFilter) return false;
    if (severityFilter && d.worstSeverity !== severityFilter) return false;
    if (search && !d.id.includes(search)) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Review Queue</h1>
        <p className="mt-1 text-sm text-gray-500">
          {filtered.length} document{filtered.length !== 1 ? "s" : ""}
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input w-48 pl-8 text-sm"
          />
        </div>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as any)} className="select w-32 text-sm">
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="in_review">In Review</option>
          <option value="resolved">Resolved</option>
        </select>
        <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value as any)} className="select w-32 text-sm">
          <option value="">All Severity</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="ADVISORY">Advisory</option>
        </select>
        {(statusFilter || severityFilter || search) && (
          <button onClick={() => { setStatusFilter(""); setSeverityFilter(""); setSearch(""); }} className="text-sm font-medium text-indigo-600 hover:text-indigo-500">
            Clear filters
          </button>
        )}
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              {["Severity", "Document", "Type", "Flags", "Status", "Submitted"].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-xs font-medium text-gray-500">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((doc) => {
              const st = STATUS_STYLE[doc.status];
              return (
                <tr key={doc.id} className="transition-colors hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <SeverityBadge severity={doc.worstSeverity} />
                  </td>
                  <td className="px-4 py-3">
                    <Link href={`/documents/${doc.id}`} className="font-mono text-sm font-medium text-indigo-600 hover:text-indigo-500">
                      {doc.id}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 capitalize">{doc.documentType}</td>
                  <td className="px-4 py-3">
                    <span className="text-sm font-medium text-gray-900">{doc.flagCount}</span>
                    <span className="ml-2 text-xs text-gray-400">
                      {doc.summary.critical > 0 && <span className="text-severity-critical">{doc.summary.critical}C </span>}
                      {doc.summary.high > 0 && <span className="text-severity-high">{doc.summary.high}H </span>}
                      {doc.summary.medium > 0 && <span className="text-severity-medium">{doc.summary.medium}M </span>}
                      {doc.summary.advisory > 0 && <span className="text-severity-advisory">{doc.summary.advisory}A</span>}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`badge ${st.cls}`}>{st.label}</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {new Date(doc.submittedAt).toLocaleDateString()}
                  </td>
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="py-12 text-center text-sm text-gray-400">
                  No documents match filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="text-center text-xs text-gray-400">
        Press <span className="kbd">?</span> for keyboard shortcuts
      </div>
    </div>
  );
}
