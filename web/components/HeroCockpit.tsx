"use client";

/**
 * Hero cockpit — ported exactly from the ScoutVeda homepage prototype
 * (artifact scoutveda-homepage, latest version, 26 Nov 2026).
 *
 * This replaces BOTH of the old hero mocks:
 * - the standalone OpportunityDial ring scoring a fake "82" (washed out,
 *   low contrast, no product behind it), and
 * - the BrowserShowcase auto-rotating carousel (invented earbuds 88/64/41,
 *   fake "AI-Optimized Title" for a cheap earphone, wrong 12% referral
 *   fee and ₹835.12 net profit slide).
 *
 * The panel shows ONE demo record — Phone Case iPhone 17 Grey, ₹499,
 * BSR #1,240, 4.3★ (2,184 reviews), 7 sellers, est. 1,240 units/mo*,
 * Opportunity 86/100 — and the verdict card below it reconciles the
 * ₹499 selling price down to ₹207 net profit (41.5% margin) line by line,
 * so the score is never a mystery number on its own. No floating chips,
 * no mouse tilt, no fake phone shape — Boss called the 3D phone "weird"
 * and asked for it to be removed, so it is not here.
 *
 * Margin note: the cockpit used to say 38.2% in PR #4. That was wrong:
 * ₹207 / ₹499 = 41.5%, which is what the calculator shows. Fixed here.
 */
export default function HeroCockpit() {
  return (
    <>
      <div className="sv-art-cockpit sv-reveal sv-rv-scale">
        <div className="sv-art-cockpit-head">
          <div>
            <span className="sv-art-cockpit-tag">Demo product · Cases, Covers &amp; Skins</span>
            <h3>Phone Case — iPhone 17, Grey</h3>
            <p className="sv-art-cockpit-sub">
              One complete record — price, rank, demand, competition and true margin, in a single panel.
            </p>
          </div>
          <div className="sv-art-cockpit-score">
            <span>Opportunity Score</span>
            <strong>86 / 100</strong>
            <small>Strong</small>
          </div>
        </div>
        <div className="sv-art-cockpit-grid">
          <div><span>Selling price</span><strong>₹499</strong><small>MRP ₹999</small></div>
          <div><span>Best Seller Rank</span><strong>#1,240</strong><small>Cases &amp; Covers</small></div>
          <div><span>Rating</span><strong>4.3 ★</strong><small>2,184 ratings</small></div>
          <div><span>Sellers competing</span><strong>7</strong><small>Low competition</small></div>
          <div><span>Est. monthly sales*</span><strong>1,240 units</strong><small>Estimate, not exact</small></div>
          <div><span>Net profit / unit</span><strong className="good">₹207</strong><small>41.5% margin</small></div>
        </div>
      </div>

      <div className="sv-art-verdict sv-reveal sv-rv-scale">
        <div className="sv-art-verdict-head">
          <b>Why this product scores 86 — the full maths, not just a number</b>
          <span>Demo record · Easy Ship · Fees verified Nov 2025</span>
        </div>
        <div className="sv-art-waterfall sv-reveal-group">
          <div className="sv-art-wf"><span>Selling price</span><strong>₹499</strong><small>Cases &amp; Covers</small></div>
          <div className="sv-art-wf"><span>Referral fee</span><strong>₹0</strong><small>0% up to ₹1,000</small></div>
          <div className="sv-art-wf"><span>Closing + shipping</span><strong>−₹78</strong><small>₹23 + ₹55 Easy Ship</small></div>
          <div className="sv-art-wf"><span>GST on fees</span><strong>−₹14</strong><small>18% of ₹78</small></div>
          <div className="sv-art-wf"><span>Your cost</span><strong>−₹200</strong><small>Buying cost</small></div>
          <div className="sv-art-wf good"><span>Net profit</span><strong>₹207</strong><small>41.5% margin</small></div>
        </div>
      </div>
      <p className="sv-art-est-note">*Sales figures are estimates, never exact.</p>
    </>
  );
}
