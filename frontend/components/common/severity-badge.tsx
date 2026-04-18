import { AlertTriangle, AlertCircle, Info, XCircle } from "lucide-react";

/**
 * SeverityBadge — minimal style.
 * Color + icon + text. NEVER green. (§5.7)
 */

type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "ADVISORY";

const config: Record<
  Severity,
  { bg: string; text: string; Icon: typeof XCircle }
> = {
  CRITICAL: { bg: "bg-severity-critical-bg", text: "text-severity-critical", Icon: XCircle },
  HIGH:     { bg: "bg-severity-high-bg",     text: "text-severity-high",     Icon: AlertTriangle },
  MEDIUM:   { bg: "bg-severity-medium-bg",   text: "text-severity-medium",   Icon: AlertCircle },
  ADVISORY: { bg: "bg-severity-advisory-bg", text: "text-severity-advisory", Icon: Info },
};

interface SeverityBadgeProps {
  severity: Severity;
  className?: string;
}

export function SeverityBadge({ severity, className = "" }: SeverityBadgeProps) {
  const { bg, text, Icon } = config[severity];

  return (
    <span className={`badge ${bg} ${text} ${className}`}>
      <Icon className="h-3 w-3" aria-hidden="true" />
      {severity}
    </span>
  );
}
