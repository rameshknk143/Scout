"use client";

/**
 * Hero cockpit — ported exactly from the ScoutVeda homepage prototype
 * (artifact scoutveda-homepage, version v6, 26 Nov 2026, approved by Boss).
 *
 * ONE unified professional panel, not the old two-part layout it replaces:
 * - old: six-tile grid (sv-art-cockpit) + separate verdict waterfall card
 *   (sv-art-verdict) repeating the same numbers.
 * - new: header with price + Opportunity Score block with score bar,
 *   a 4-cell divided KPI strip, and a clean profit ledger ending in a
 *   highlighted green total row.
 *
 * Shows ONE demo record — Phone Case iPhone 17 Grey, ₹499, BSR #1,240,
 * 4.3★ (2,184 reviews), 7 sellers, est. 1,240 units/mo*, Opportunity
 * 86/100 — and the ledger reconciles ₹499 down to ₹207 net profit
 * (41.5% margin) line by line. No floating chips, no mouse tilt, no
 * fake phone shape — Boss called the 3D phone "weird" and asked for it
 * to be removed, so it is not here.
 */
export default function HeroCockpit() {
  return (
    <>
      <div className="sv-art-ck sv-reveal sv-rv-scale">
        <div className="sv-art-ck-head">
          <div>
            <span className="sv-art-ck-tag">Demo record · Cases, Covers &amp; Skins</span>
            <h3>Phone Case — iPhone 17, Grey</h3>
            <div className="sv-art-ck-meta">
              <span className="sv-art-ck-price">₹499</span>
              <span className="sv-art-ck-mrp">MRP <s>₹999</s></span>
              <span className="sv-art-ck-save">50% off MRP</span>
            </div>
          </div>
          <div className="sv-art-ck-score">
            <div className="sv-art-ck-score-top">
              <span>Opportunity Score</span>
              <span className="sv-art-ck-badge">Strong</span>
            </div>
            <div className="sv-art-ck-score-num">86<small> / 100</small></div>
            <div className="sv-art-ck-bar"><i style={{ width: "86%" }} /></div>
          </div>
        </div>
        <div className="sv-art-ck-kpis">
          <div className="sv-art-ck-kpi"><span>Best Seller Rank</span><strong>#1,240</strong><small>Cases &amp; Covers</small></div>
          <div className="sv-art-ck-kpi"><span>Rating</span><strong>4.3 <span className="sv-art-ck-star">★</span></strong><small>2,184 ratings</small></div>
          <div className="sv-art-ck-kpi"><span>Sellers competing</span><strong>7</strong><small>Low competition</small></div>
          <div className="sv-art-ck-kpi"><span>Est. monthly sales*</span><strong>1,240 units</strong><small>Estimate, not exact</small></div>
        </div>
        <div className="sv-art-ck-profit">
          <div className="sv-art-ck-profit-head"><b>Profit breakdown — per unit</b><span>Easy Ship · Amazon.in fees verified Nov 2025</span></div>
          <div className="sv-art-ck-row"><span>Selling price</span><b>₹499</b></div>
          <div className="sv-art-ck-row"><span>Referral fee<small>0% up to ₹1,000 in this category</small></span><b>₹0</b></div>
          <div className="sv-art-ck-row"><span>Closing + shipping<small>₹23 closing + ₹55 Easy Ship</small></span><b>−₹78</b></div>
          <div className="sv-art-ck-row"><span>GST on fees<small>18% of ₹78</small></span><b>−₹14</b></div>
          <div className="sv-art-ck-row"><span>Your buying cost</span><b>−₹200</b></div>
          <div className="sv-art-ck-row sv-art-ck-total"><span>Net profit / unit</span><span className="sv-art-ck-total-r"><span className="sv-art-ck-margin">41.5% margin</span><b>₹207</b></span></div>
        </div>
      </div>
      <p className="sv-art-est-note">*Sales figures are estimates, never exact.</p>
    </>
  );
}
