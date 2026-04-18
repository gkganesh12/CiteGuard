"use client";

import { ExternalLink } from "lucide-react";

export default function BillingPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Billing</h1>
        <p className="mt-1 text-sm text-gray-500">Subscription and usage.</p>
      </div>

      <div className="max-w-2xl space-y-4">
        <div className="card p-6">
          <p className="text-xs font-medium uppercase tracking-wide text-gray-400">Current Plan</p>
          <p className="mt-2 text-2xl font-semibold text-gray-900">Firm Plan</p>
          <p className="mt-1 text-sm text-gray-500">$1,500/mo + $2 per document</p>
        </div>

        <div className="card">
          <div className="border-b border-gray-200 px-5 py-3">
            <h2 className="text-sm font-medium text-gray-900">Current Period</h2>
          </div>
          <div className="grid grid-cols-2 gap-6 p-5">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-gray-400">Documents</p>
              <p className="mt-1 text-2xl font-semibold text-gray-900">0</p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-gray-400">Usage Charges</p>
              <p className="mt-1 text-2xl font-semibold text-gray-900">$0.00</p>
            </div>
          </div>
        </div>

        <button className="btn-secondary w-full justify-center">
          <ExternalLink className="h-4 w-4" /> Manage in Stripe
        </button>
      </div>
    </div>
  );
}
