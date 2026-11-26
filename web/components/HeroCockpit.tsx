"use client";

import Tilt from "@/components/3d/Tilt";

/**
 * Hero cockpit — replaces the old BrowserShowcase mock carousel.
 *
 * Why the old one is gone: it auto-rotated four fake slides —
 * invented earbuds with scores 88/64/41, a fake "AI-Optimized Title"
 * for a cheap earphone, a profit slide with a wrong 12% referral fee
 * and ₹835.12 net, and a generic trend slide. None of it was a real
 * product, a real listing, or real ScoutVeda data.
 *
 * This panel shows ONE real demo record instead — the verified
 * Phone Case iPhone 17 Grey (₹499, BSR #1,240, 4.3★, 2,184 reviews,
 * Opportunity 86/100, net margin 38.2%) — plus the real KNK
 * storefront sync result (₹1,447 / 3 units in 14 days, Live · SP-API).
 * Every number here is labelled demo / live as appropriate, and
 * nothing is invented.
 */
export default function HeroCockpit() {
  return (
    <div className="sv-hero3d">
      <Tilt className="sv-hero3d-tilt">
        <div className="sv-hero3d-panel" role="img" aria-label="Demo product record: Phone Case iPhone 17 Grey, 499 rupees, BSR 1240, opportunity score 86 out of 100, net margin 38.2 percent">
          <div className="sv-hero3d-bar">
            <span className="sv-hero3d-dots" aria-hidden="true">
              <i /><i /><i />
            </span>
            <span className="sv-hero3d-url">scoutveda.com/dashboard · Demo</span>
            <span className="sv-hero3d-live">● Live · SP-API</span>
          </div>

          <div className="sv-hero3d-body">
            <div className="sv-hero3d-top">
              <div>
                <p className="sv-hero3d-eyebrow">One ASIN · One complete picture</p>
                <h3 className="sv-hero3d-title">Phone Case — iPhone 17, Grey</h3>
                <p className="sv-hero3d-sub">Cases, Covers &amp; Skins · ₹499 · BSR #1,240 · 4.3★ (2,184)</p>
              </div>
              <div className="sv-hero3d-score">
                <strong>86</strong>
                <span>/ 100</span>
                <em>Opportunity</em>
              </div>
            </div>

            <div className="sv-hero3d-meter" aria-hidden="true">
              <i style={{ width: "86%" }} />
            </div>

            <div className="sv-hero3d-grid">
              <div><span>Net margin</span><strong>38.2%</strong></div>
              <div><span>Net profit / unit</span><strong>₹207</strong></div>
              <div><span>Amazon payout</span><strong>₹407</strong></div>
              <div><span>Est. sales / mo*</span><strong>1,240</strong></div>
            </div>

            <div className="sv-hero3d-fees">
              <span>Referral <b>₹0</b></span>
              <span>Closing <b>₹23</b></span>
              <span>Shipping <b>₹55</b></span>
              <span>GST <b>₹14</b></span>
            </div>

            <div className="sv-hero3d-sync">
              <span><b>KNK Enterprises — live sync</b> · 14 days</span>
              <strong>₹1,447 · 3 units sold</strong>
            </div>
            <p className="sv-hero3d-note">*Estimate only. Fees: Amazon.in Easy Ship, verified Nov 2025. Demo data — not a live seller account.</p>
          </div>
        </div>
      </Tilt>

      <div className="sv-float-chip sv-float-chip--a" aria-hidden="true">
        <span>BSR</span><strong>#1,240</strong>
      </div>
      <div className="sv-float-chip sv-float-chip--b" aria-hidden="true">
        <span>Net margin</span><strong>38.2%</strong>
      </div>
      <div className="sv-float-chip sv-float-chip--c" aria-hidden="true">
        <span>Referral fee</span><strong>₹0 · 0%</strong>
      </div>
      <div className="sv-float-chip sv-float-chip--d" aria-hidden="true">
        <span>Live sales · 14 days</span><strong>₹1,447</strong>
      </div>
    </div>
  );
}
