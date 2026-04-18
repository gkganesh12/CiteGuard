"use client";

import { useState } from "react";
import { UserPlus } from "lucide-react";

type Role = "admin" | "reviewer" | "submitter";

const ROLE_STYLE: Record<Role, { label: string; cls: string }> = {
  admin:     { label: "Admin",     cls: "bg-indigo-50 text-indigo-700" },
  reviewer:  { label: "Reviewer",  cls: "bg-amber-50 text-amber-700" },
  submitter: { label: "Submitter", cls: "bg-gray-100 text-gray-600" },
};

export default function TeamPage() {
  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<Role>("submitter");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Team</h1>
          <p className="mt-1 text-sm text-gray-500">Manage members and roles.</p>
        </div>
        <button onClick={() => setShowInvite(true)} className="btn-primary text-sm">
          <UserPlus className="h-4 w-4" /> Invite
        </button>
      </div>

      <div className="flex gap-2">
        {(Object.entries(ROLE_STYLE) as [Role, { label: string; cls: string }][]).map(([, v]) => (
          <span key={v.label} className={`badge ${v.cls}`}>{v.label}</span>
        ))}
      </div>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              {["Email", "Role", "Last Login", "Actions"].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-xs font-medium text-gray-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={4} className="py-12 text-center text-sm text-gray-400">
                No team members yet. Invite your first member.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {showInvite && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="w-96 rounded-lg border border-gray-200 bg-white p-6 shadow-lg">
            <h3 className="text-sm font-semibold text-gray-900">Invite Member</h3>
            <div className="mt-4 space-y-3">
              <div>
                <label className="label">Email</label>
                <input type="email" value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} className="input mt-1" placeholder="colleague@firm.com" autoFocus />
              </div>
              <div>
                <label className="label">Role</label>
                <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value as Role)} className="select mt-1">
                  <option value="submitter">Submitter</option>
                  <option value="reviewer">Reviewer</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <button onClick={() => setShowInvite(false)} className="btn-secondary text-sm">Cancel</button>
              <button disabled={!inviteEmail} className="btn-primary text-sm">Send Invite</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
