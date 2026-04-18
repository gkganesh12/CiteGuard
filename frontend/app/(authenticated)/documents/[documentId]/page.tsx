"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { Check, RotateCcw, X, ArrowLeftRight, Download } from "lucide-react";
import { SeverityBadge } from "@/components/common/severity-badge";

type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "ADVISORY";
type Action = "approve" | "override" | "reject" | "defer";

interface Flag {
  id: string; evaluator: string; severity: Severity; explanation: string;
  confidence: number; startOffset: number; endOffset: number;
  suggestedCorrection: string | null; action: Action | null; reason: string | null;
}

const MOCK_TEXT = `In Smith v. Jones, 123 F.3d 456 (9th Cir. 2019), the court held that summary judgment is appropriate when there is no genuine dispute as to any material fact. The court further stated that "the moving party bears the initial burden of demonstrating the absence of a genuine issue of material fact." Smith v. Jones, 123 F.3d 456, 461 (9th Cir. 2019).

Judge Robert Henderson, writing for the majority, emphasized that the standard requires more than mere speculation. See also Doe v. Roe, 789 F.Supp.2d 101 (S.D.N.Y. 2021) (applying the same standard in the employment context).

As noted in Williams v. State, 456 U.S. 789 (1985), the burden then shifts to the non-moving party to establish a genuine dispute. This precedent has been consistently followed across circuits.`;

const MOCK_FLAGS: Flag[] = [
  { id: "f1", evaluator: "citation_existence", severity: "CRITICAL", explanation: "Citation '123 F.3d 456 (9th Cir. 2019)' does not match any opinion in CourtListener. This citation may be hallucinated.", confidence: 0.95, startOffset: 22, endOffset: 54, suggestedCorrection: null, action: null, reason: null },
  { id: "f2", evaluator: "quote_verification", severity: "CRITICAL", explanation: "Quoted passage does not appear in the cited opinion (similarity: 12%). This quote may be fabricated.", confidence: 0.92, startOffset: 145, endOffset: 245, suggestedCorrection: null, action: null, reason: null },
  { id: "f3", evaluator: "judge_verification", severity: "HIGH", explanation: "No federal judge named 'Robert Henderson' found in the FJC Biographical Directory.", confidence: 0.88, startOffset: 310, endOffset: 345, suggestedCorrection: null, action: null, reason: null },
  { id: "f4", evaluator: "bluebook_format", severity: "MEDIUM", explanation: "Incorrect reporter abbreviation 'F.Supp.2d'. Bluebook requires 'F. Supp. 2d'.", confidence: 0.9, startOffset: 435, endOffset: 470, suggestedCorrection: "789 F. Supp. 2d 101", action: null, reason: null },
  { id: "f5", evaluator: "temporal_validity", severity: "ADVISORY", explanation: "No negative treatment found for '456 U.S. 789 (1985)'. Citation is temporally valid.", confidence: 0.6, startOffset: 520, endOffset: 550, suggestedCorrection: null, action: null, reason: null },
];

const EVAL_LABELS: Record<string, string> = {
  citation_existence: "Citation Exists", quote_verification: "Quote Check",
  judge_verification: "Judge Check", bluebook_format: "Bluebook", temporal_validity: "Temporal",
};

const SEV_ORDER: Record<Severity, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, ADVISORY: 3 };

export default function DocumentDetailPage() {
  const params = useParams();
  const documentId = params.documentId as string;
  const [flags, setFlags] = useState<Flag[]>([...MOCK_FLAGS].sort((a, b) => SEV_ORDER[a.severity] - SEV_ORDER[b.severity]));
  const [sel, setSel] = useState(0);
  const [overrideReason, setOverrideReason] = useState("");
  const [showOverride, setShowOverride] = useState(false);

  const selected = flags[sel] || null;
  const unresolved = flags.filter((f) => !f.action).length;

  const handleAction = (action: Action, reason?: string) => {
    setFlags((p) => p.map((f, i) => (i === sel ? { ...f, action, reason: reason || null } : f)));
    setShowOverride(false);
    setOverrideReason("");
    const next = flags.findIndex((f, i) => i > sel && !f.action);
    if (next >= 0) setSel(next);
  };

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
    switch (e.key.toLowerCase()) {
      case "j": setSel((i) => Math.min(i + 1, flags.length - 1)); break;
      case "k": setSel((i) => Math.max(i - 1, 0)); break;
      case "a": if (selected && !selected.action) handleAction("approve"); break;
      case "o": if (selected && !selected.action) setShowOverride(true); break;
      case "r": if (selected && !selected.action) handleAction("reject"); break;
      case "d": if (selected && !selected.action) handleAction("defer"); break;
    }
  }, [selected, flags.length, sel]);

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  const sevBorder: Record<Severity, string> = {
    CRITICAL: "border-l-severity-critical",
    HIGH: "border-l-severity-high",
    MEDIUM: "border-l-severity-medium",
    ADVISORY: "border-l-severity-advisory",
  };

  const sevHighlight: Record<Severity, string> = {
    CRITICAL: "bg-severity-critical/10 decoration-severity-critical",
    HIGH: "bg-severity-high/10 decoration-severity-high",
    MEDIUM: "bg-severity-medium/10 decoration-severity-medium",
    ADVISORY: "bg-severity-advisory/10 decoration-severity-advisory",
  };

  return (
    <div className="flex h-[calc(100vh-3.5rem)] gap-0">
      {/* Document */}
      <div className="flex-1 overflow-y-auto border-r border-gray-200 bg-white p-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="font-mono text-sm font-medium text-gray-500">{documentId}</h1>
            <div className="mt-1 flex items-center gap-2">
              <span className="badge bg-blue-50 text-blue-700">In Review</span>
              <span className="text-xs text-gray-400">{unresolved}/{flags.length} unresolved</span>
            </div>
          </div>
          <div className="flex gap-2">
            <button disabled={unresolved > 0} className="btn-primary text-sm disabled:opacity-30">Finalize</button>
            <button className="btn-secondary p-2"><Download className="h-4 w-4" /></button>
          </div>
        </div>

        <div className="max-w-none text-base leading-relaxed text-gray-800">
          {renderHighlighted(MOCK_TEXT, flags, sel, sevHighlight)}
        </div>
      </div>

      {/* Side panel */}
      <div className="w-[380px] flex-shrink-0 overflow-y-auto bg-gray-50">
        <div className="border-b border-gray-200 bg-white px-4 py-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-gray-900">Flags ({flags.length})</h2>
            <span className="text-xs text-gray-400">
              <span className="kbd">J</span>/<span className="kbd">K</span> nav
            </span>
          </div>
        </div>

        <div className="divide-y divide-gray-200">
          {flags.map((flag, i) => (
            <div
              key={flag.id}
              onClick={() => setSel(i)}
              className={`cursor-pointer border-l-2 px-4 py-3 transition-colors ${sevBorder[flag.severity]} ${
                i === sel ? "bg-white shadow-sm" : "bg-transparent hover:bg-white/60"
              } ${flag.action ? "opacity-50" : ""}`}
            >
              <div className="flex items-center justify-between">
                <SeverityBadge severity={flag.severity} />
                {flag.action && (
                  <span className="badge bg-gray-100 text-gray-600 capitalize">{flag.action}</span>
                )}
              </div>
              <p className="mt-1.5 text-xs font-medium text-gray-500">
                {EVAL_LABELS[flag.evaluator] || flag.evaluator}
              </p>
              <p className="mt-1 line-clamp-2 text-sm text-gray-600">{flag.explanation}</p>
              <p className="mt-1 text-xs text-gray-400">
                Confidence: {(flag.confidence * 100).toFixed(0)}%
              </p>

              {i === sel && !flag.action && (
                <div className="mt-3 flex gap-1.5">
                  <button onClick={(e) => { e.stopPropagation(); handleAction("approve"); }} className="btn-primary py-1.5 px-2.5 text-xs">
                    <Check className="h-3 w-3" /><span className="kbd text-[8px] bg-white/20 text-white border-white/30">A</span>
                  </button>
                  <button onClick={(e) => { e.stopPropagation(); setShowOverride(true); }} className="btn-secondary py-1.5 px-2.5 text-xs">
                    <ArrowLeftRight className="h-3 w-3" /><span className="kbd text-[8px]">O</span>
                  </button>
                  <button onClick={(e) => { e.stopPropagation(); handleAction("reject"); }} className="btn-secondary py-1.5 px-2.5 text-xs">
                    <X className="h-3 w-3" /><span className="kbd text-[8px]">R</span>
                  </button>
                  <button onClick={(e) => { e.stopPropagation(); handleAction("defer"); }} className="btn-secondary py-1.5 px-2.5 text-xs">
                    <RotateCcw className="h-3 w-3" /><span className="kbd text-[8px]">D</span>
                  </button>
                </div>
              )}

              {flag.suggestedCorrection && i === sel && (
                <div className="mt-2 rounded-md bg-indigo-50 p-2.5">
                  <p className="text-[10px] font-medium uppercase tracking-wide text-indigo-400">Suggested fix</p>
                  <p className="mt-0.5 font-mono text-sm text-indigo-700">{flag.suggestedCorrection}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Override modal */}
      {showOverride && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="w-96 rounded-lg border border-gray-200 bg-white p-6 shadow-lg">
            <h3 className="text-sm font-semibold text-gray-900">Override Flag</h3>
            <p className="mt-1 text-xs text-gray-500">Min 10 characters required.</p>
            <textarea
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              className="input mt-4 min-h-[80px]"
              placeholder="Reason for override..."
              autoFocus
            />
            <p className="mt-1 text-xs text-gray-400">{overrideReason.length}/10 min</p>
            <div className="mt-4 flex justify-end gap-2">
              <button onClick={() => { setShowOverride(false); setOverrideReason(""); }} className="btn-secondary text-sm">Cancel</button>
              <button onClick={() => handleAction("override", overrideReason)} disabled={overrideReason.length < 10} className="btn-primary text-sm">Submit</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function renderHighlighted(text: string, flags: Flag[], selectedIndex: number, sevHighlight: Record<Severity, string>) {
  const hl = flags.filter((f) => f.startOffset >= 0 && f.endOffset > f.startOffset).sort((a, b) => a.startOffset - b.startOffset);
  if (!hl.length) return <p className="whitespace-pre-wrap">{text}</p>;

  const segs: React.ReactNode[] = [];
  let last = 0;
  hl.forEach((h) => {
    const fi = flags.indexOf(h);
    const s = Math.min(h.startOffset, text.length);
    const e = Math.min(h.endOffset, text.length);
    if (s > last) segs.push(<span key={`t${last}`}>{text.slice(last, s)}</span>);
    segs.push(
      <mark
        key={h.id}
        className={`cursor-pointer rounded-sm underline decoration-wavy decoration-1 underline-offset-4 ${sevHighlight[h.severity]} ${
          fi === selectedIndex ? "ring-2 ring-indigo-400 ring-offset-1" : ""
        } ${h.action ? "opacity-30 line-through" : ""}`}
        title={`${h.severity}: ${h.explanation}`}
      >
        {text.slice(s, e)}
      </mark>
    );
    last = e;
  });
  if (last < text.length) segs.push(<span key="end">{text.slice(last)}</span>);
  return <p className="whitespace-pre-wrap">{segs}</p>;
}
