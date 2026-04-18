"use client";

import { useState } from "react";
import { Plus, Copy, Check, Key } from "lucide-react";

export default function APIKeysPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [keyName, setKeyName] = useState("");
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCreate = () => {
    const fakeKey = `cg_live_${Array.from({ length: 32 }, () => Math.random().toString(36)[2]).join("")}`;
    setNewKey(fakeKey);
  };

  const handleCopy = () => {
    if (newKey) { navigator.clipboard.writeText(newKey); setCopied(true); setTimeout(() => setCopied(false), 2000); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">API Keys</h1>
          <p className="mt-1 text-sm text-gray-500">SDK and proxy authentication.</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary text-sm">
          <Plus className="h-4 w-4" /> Generate
        </button>
      </div>

      <div className="rounded-lg border border-severity-medium/30 bg-severity-medium-bg p-4">
        <p className="text-sm font-medium text-severity-medium">
          API keys are shown once at creation. Store them securely. CiteGuard cannot recover lost keys.
        </p>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              {["Name", "Prefix", "Created", "Last Used", "Actions"].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-xs font-medium text-gray-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={5} className="py-16 text-center">
                <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-gray-100">
                  <Key className="h-5 w-5 text-gray-400" />
                </div>
                <p className="text-sm font-medium text-gray-500">No keys yet</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {showCreate && !newKey && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="w-96 rounded-lg border border-gray-200 bg-white p-6 shadow-lg">
            <h3 className="text-sm font-semibold text-gray-900">Generate API Key</h3>
            <div className="mt-4">
              <label className="label">Key Name</label>
              <input type="text" value={keyName} onChange={(e) => setKeyName(e.target.value)} className="input mt-1" placeholder="e.g., Production SDK" autoFocus />
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <button onClick={() => { setShowCreate(false); setKeyName(""); }} className="btn-secondary text-sm">Cancel</button>
              <button onClick={handleCreate} disabled={!keyName} className="btn-primary text-sm">Generate</button>
            </div>
          </div>
        </div>
      )}

      {newKey && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="w-[480px] rounded-lg border border-gray-200 bg-white p-6 shadow-lg">
            <h3 className="text-sm font-semibold text-gray-900">Key Created</h3>
            <p className="mt-1 text-xs font-medium text-severity-critical">Copy now. This key is shown once.</p>
            <div className="mt-4 flex items-center gap-2 rounded-md bg-gray-50 p-3">
              <code className="flex-1 break-all font-mono text-xs text-gray-700">{newKey}</code>
              <button onClick={handleCopy} className="btn-secondary p-1.5">
                {copied ? <Check className="h-4 w-4 text-indigo-600" /> : <Copy className="h-4 w-4" />}
              </button>
            </div>
            <div className="mt-6 flex justify-end">
              <button onClick={() => { setNewKey(null); setShowCreate(false); setKeyName(""); }} className="btn-primary text-sm">
                I saved this key
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
