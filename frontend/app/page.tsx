"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Link from "next/link";
import { ArrowRight, Check, Shield } from "lucide-react";

gsap.registerPlugin(ScrollTrigger);

const DEMO_TERMINAL = `$ citeguard verify brief.txt

  Parsing citations ............ done (14 found)

  ┌─────┬──────────┬─────────────────────┬────────┐
  │  #  │ SEVERITY │ EVALUATOR           │ RESULT │
  ├─────┼──────────┼─────────────────────┼────────┤
  │  1  │ CRITICAL │ citation_existence  │ FAKE   │
  │  2  │ CRITICAL │ quote_verification  │ FAKE   │
  │  3  │ HIGH     │ judge_verification  │ WRONG  │
  │  4  │ MEDIUM   │ bluebook_format     │ FIX    │
  │  5  │ ADVISORY │ temporal_validity   │ OK     │
  └─────┴──────────┴─────────────────────┴────────┘

  2 CRITICAL | 1 HIGH | 1 MEDIUM | 1 ADVISORY

  Review at: https://app.citeguard.ai/doc/cg_abc123`;

export default function LandingPage() {
  const cardsRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".hero-content > *",
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, stagger: 0.1, duration: 0.6, ease: "power2.out", delay: 0.1 }
      );

      gsap.fromTo(
        ".feature-card",
        { opacity: 0, y: 30 },
        {
          opacity: 1, y: 0, stagger: 0.08, duration: 0.5,
          ease: "power2.out",
          scrollTrigger: { trigger: cardsRef.current, start: "top 80%" },
        }
      );

      gsap.fromTo(
        termRef.current,
        { opacity: 0, y: 20 },
        {
          opacity: 1, y: 0, duration: 0.6,
          ease: "power2.out",
          scrollTrigger: { trigger: termRef.current, start: "top 80%" },
        }
      );

      gsap.fromTo(
        ".pricing-card",
        { opacity: 0, y: 20 },
        {
          opacity: 1, y: 0, duration: 0.5,
          scrollTrigger: { trigger: ".pricing-card", start: "top 85%" },
        }
      );
    });
    return () => ctx.revert();
  }, []);

  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-gray-100 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gray-900">
              <Shield className="h-4 w-4 text-white" />
            </div>
            <span className="text-sm font-semibold tracking-tight">CiteGuard</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/sign-in" className="btn-secondary text-sm">
              Sign In
            </Link>
            <Link href="/sign-up" className="btn-primary text-sm">
              Get Started <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="py-24">
        <div className="mx-auto max-w-5xl px-6">
          <div className="hero-content mx-auto max-w-2xl text-center">
            <div className="badge border border-indigo-200 bg-indigo-50 text-indigo-600">
              V1 Launch
            </div>
            <h1 className="mt-6 text-4xl font-semibold leading-tight tracking-tight text-gray-900 sm:text-5xl">
              AI writes briefs.
              <br />
              We catch the lies.
            </h1>
            <p className="mt-5 text-lg text-gray-500">
              5 deterministic evaluators. Zero hallucinations reaching court.
              Tamper-evident audit trails that satisfy malpractice carriers.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Link href="/sign-up" className="btn-primary">
                Start Free Trial <ArrowRight className="h-4 w-4" />
              </Link>
              <a href="#demo" className="btn-secondary">
                See It Work
              </a>
            </div>
            <p className="mt-4 text-xs text-gray-400">
              No credit card. 14-day trial. $1,500/mo after.
            </p>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-y border-gray-100 bg-gray-50 py-6">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-6 px-6">
          {[
            ["5", "Evaluators"],
            ["95%+", "True-positive rate"],
            ["<3s", "P95 latency"],
            ["SHA-256", "Hash chain"],
            ["0", "Hallucinations past CiteGuard"],
          ].map(([val, label]) => (
            <div key={label} className="text-center">
              <div className="text-xl font-semibold text-gray-900">{val}</div>
              <div className="text-xs text-gray-500">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section ref={cardsRef} className="py-24">
        <div className="mx-auto max-w-5xl px-6">
          <p className="text-center text-xs font-medium uppercase tracking-wide text-gray-400">
            What We Catch
          </p>
          <h2 className="mt-2 text-center text-2xl font-semibold text-gray-900">
            Five checks. Every document. No LLM in the loop.
          </h2>

          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { num: "01", title: "Citation Existence", desc: "Is this case real? Verified against 8M+ opinions in CourtListener.", tag: "Critical if fake", tagCls: "bg-severity-critical-bg text-severity-critical" },
              { num: "02", title: "Quote Verification", desc: "Did the court actually say that? Fuzzy-matched at 85% threshold.", tag: "Critical if fabricated", tagCls: "bg-severity-critical-bg text-severity-critical" },
              { num: "03", title: "Bluebook Formatting", desc: "21st edition rules. Abbreviations, pincites, parentheticals.", tag: "Medium / High", tagCls: "bg-severity-medium-bg text-severity-medium" },
              { num: "04", title: "Judge Verification", desc: "Did this judge sit on this court? Checked against FJC directory.", tag: "Critical if fake", tagCls: "bg-severity-critical-bg text-severity-critical" },
              { num: "05", title: "Temporal Validity", desc: "Has this case been overruled? Citation graph analysis.", tag: "Critical / High", tagCls: "bg-severity-high-bg text-severity-high" },
              { num: "06", title: "Audit Trail", desc: "SHA-256 hash-chained log. Every action recorded. PDF exports.", tag: "Tamper-evident", tagCls: "bg-gray-100 text-gray-600" },
            ].map((f) => (
              <div
                key={f.num}
                className="feature-card card p-5 transition-shadow hover:shadow-md"
              >
                <div className="flex items-start justify-between">
                  <span className="text-2xl font-semibold text-gray-200">
                    {f.num}
                  </span>
                  <span className={`badge text-[10px] ${f.tagCls}`}>
                    {f.tag}
                  </span>
                </div>
                <h3 className="mt-3 font-semibold text-gray-900">{f.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-gray-500">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Terminal */}
      <section id="demo" className="bg-gray-950 py-24">
        <div className="mx-auto max-w-4xl px-6">
          <p className="text-center text-xs font-medium uppercase tracking-wide text-gray-500">
            Live Demo
          </p>
          <h2 className="mt-2 text-center text-2xl font-semibold text-white">
            What your terminal shows
          </h2>

          <pre
            ref={termRef}
            className="mx-auto mt-10 max-w-2xl overflow-x-auto rounded-lg border border-gray-800 bg-gray-900 p-6 font-mono text-xs leading-relaxed text-gray-300 sm:text-sm"
          >
            {DEMO_TERMINAL}
          </pre>

          <p className="mt-6 text-center text-xs text-gray-500">
            One API call. Five evaluators. Sub-3-second response.
          </p>
        </div>
      </section>

      {/* How it works */}
      <section className="py-24">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="text-center text-2xl font-semibold text-gray-900">Three steps.</h2>

          <div className="mx-auto mt-12 grid max-w-3xl gap-4 md:grid-cols-3">
            {[
              { step: "1", title: "Submit", desc: "One SDK call or paste in the dashboard." },
              { step: "2", title: "Verify", desc: "5 evaluators run in parallel. Under 3 seconds." },
              { step: "3", title: "Review", desc: "Keyboard-first queue. A/O/R/D. Finalize. Export PDF." },
            ].map((s) => (
              <div key={s.step} className="card p-6">
                <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-md bg-gray-100 text-sm font-semibold text-gray-600">
                  {s.step}
                </div>
                <h3 className="font-semibold text-gray-900">{s.title}</h3>
                <p className="mt-1.5 text-sm text-gray-500">{s.desc}</p>
              </div>
            ))}
          </div>

          <pre className="mx-auto mt-10 max-w-lg overflow-x-auto rounded-lg bg-gray-50 p-4 text-center font-mono text-xs text-gray-400">
{`Your AI Tool ──→ CiteGuard API ──→ 5 Evaluators
                      │                   │
                      ▼                   ▼
                  Audit Log ←──── Flags Created
                  (hash-chain)        │
                                      ▼
                              Review Queue (UI)
                              [A] [O] [R] [D]
                                      │
                                      ▼
                              Audit PDF Export`}
          </pre>
        </div>
      </section>

      {/* Pricing */}
      <section className="border-t border-gray-100 bg-gray-50 py-24">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="text-center text-2xl font-semibold text-gray-900">Simple pricing.</h2>
          <p className="mt-2 text-center text-sm text-gray-500">
            No per-seat fees. No contracts. Cancel anytime.
          </p>

          <div className="pricing-card mx-auto mt-10 max-w-sm card p-8">
            <span className="badge bg-gray-900 text-white">Firm Plan</span>
            <div className="mt-5 flex items-baseline gap-1">
              <span className="text-4xl font-semibold text-gray-900">$1,500</span>
              <span className="text-sm text-gray-400">/mo</span>
            </div>
            <p className="mt-1 text-sm text-gray-500">
              + $2 per document verified
            </p>

            <div className="mt-6 space-y-2.5">
              {[
                "Unlimited seats",
                "All 5 evaluators",
                "Tamper-evident audit PDFs",
                "SDK + REST proxy",
                "Slack + email alerts",
                "Keyboard-first review queue",
                "14-day free trial",
              ].map((item) => (
                <div key={item} className="flex items-center gap-2.5 text-sm text-gray-600">
                  <Check className="h-4 w-4 shrink-0 text-gray-400" />
                  {item}
                </div>
              ))}
            </div>

            <Link
              href="/sign-up"
              className="btn-primary mt-8 w-full justify-center"
            >
              Start Free Trial
            </Link>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24">
        <div className="mx-auto max-w-2xl px-6 text-center">
          <p className="mx-auto mb-6 max-w-sm rounded-lg bg-gray-50 px-6 py-4 text-sm italic text-gray-500">
            &ldquo;Nothing embarrassing reaches a judge.&rdquo;
            <span className="mt-1 block text-xs not-italic text-gray-400">
              What your managing partner wants to hear.
            </span>
          </p>
          <h2 className="text-2xl font-semibold text-gray-900">
            Stop worrying about AI hallucinations.
          </h2>
          <p className="mt-3 text-gray-500">
            CiteGuard catches what your associates miss.
          </p>
          <Link
            href="/sign-up"
            className="btn-primary mt-8"
          >
            Get Started Now <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8">
        <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-4 px-6 sm:flex-row">
          <span className="text-xs font-medium text-gray-400">CiteGuard v0.1.0</span>
          <div className="flex gap-6 text-xs text-gray-400">
            <span>Privacy</span>
            <span>Terms</span>
            <span>Security</span>
          </div>
          <span className="text-xs text-gray-400">
            Not a law firm. Not legal advice.
          </span>
        </div>
      </footer>
    </div>
  );
}
