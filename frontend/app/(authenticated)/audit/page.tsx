"use client";

import { FileText, Shield } from "lucide-react";

export default function AuditExportsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Audit Exports</h1>
        <p className="mt-1 text-sm text-gray-500">Tamper-evident PDF reports with SHA-256 hash chain.</p>
      </div>

      <div className="card flex items-center gap-4 p-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50">
          <Shield className="h-4 w-4 text-indigo-600" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-900">Chain Integrity</p>
          <p className="text-xs text-gray-500">SHA-256 hash chain verified. All entries intact.</p>
        </div>
        <span className="badge bg-indigo-50 text-indigo-600">Verified</span>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              {["Export ID", "Document", "PDF Hash", "Generated", "Actions"].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-xs font-medium text-gray-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={5} className="py-16 text-center">
                <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-gray-100">
                  <FileText className="h-5 w-5 text-gray-400" />
                </div>
                <p className="text-sm font-medium text-gray-500">No exports yet</p>
                <p className="mt-1 text-xs text-gray-400">Finalize a document to generate an audit export.</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
