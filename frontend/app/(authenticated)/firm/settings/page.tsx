"use client";

import { useState } from "react";
import { Save } from "lucide-react";

export default function FirmSettingsPage() {
  const [firmName, setFirmName] = useState("");
  const [billingEmail, setBillingEmail] = useState("");
  const [slackWebhook, setSlackWebhook] = useState("");
  const [retention, setRetention] = useState("90");
  const [saved, setSaved] = useState(false);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Settings</h1>
        <p className="mt-1 text-sm text-gray-500">Firm workspace configuration.</p>
      </div>

      <div className="max-w-2xl space-y-4">
        <div className="card">
          <div className="border-b border-gray-200 px-5 py-3">
            <h2 className="text-sm font-medium text-gray-900">General</h2>
          </div>
          <div className="space-y-4 p-5">
            <div>
              <label className="label">Firm Name</label>
              <input type="text" value={firmName} onChange={(e) => setFirmName(e.target.value)} className="input mt-1" placeholder="Acme Law LLP" />
            </div>
            <div>
              <label className="label">Billing Email</label>
              <input type="email" value={billingEmail} onChange={(e) => setBillingEmail(e.target.value)} className="input mt-1" placeholder="billing@acmelaw.com" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="border-b border-gray-200 px-5 py-3">
            <h2 className="text-sm font-medium text-gray-900">Slack Alerts</h2>
          </div>
          <div className="p-5">
            <label className="label">Webhook URL</label>
            <input type="url" value={slackWebhook} onChange={(e) => setSlackWebhook(e.target.value)} className="input mt-1" placeholder="https://hooks.slack.com/services/..." />
            <p className="mt-1.5 text-xs text-gray-400">Critical flags trigger alerts within 60 seconds.</p>
          </div>
        </div>

        <div className="card">
          <div className="border-b border-gray-200 px-5 py-3">
            <h2 className="text-sm font-medium text-gray-900">Data Retention</h2>
          </div>
          <div className="p-5">
            <label className="label">Document Retention</label>
            <select value={retention} onChange={(e) => setRetention(e.target.value)} className="select mt-1">
              <option value="90">90 days (default)</option>
              <option value="365">1 year</option>
              <option value="1095">3 years</option>
              <option value="2555">7 years</option>
            </select>
            <p className="mt-1.5 text-xs text-gray-400">Audit log always retained 7 years minimum.</p>
          </div>
        </div>

        <div className="flex justify-end">
          <button onClick={() => { setSaved(true); setTimeout(() => setSaved(false), 2000); }} className="btn-primary text-sm">
            <Save className="h-4 w-4" />
            {saved ? "Saved" : "Save Settings"}
          </button>
        </div>
      </div>
    </div>
  );
}
