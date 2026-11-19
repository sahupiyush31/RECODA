// Clean 2D doughnut chart with a subtle hover lift.
// The public class name is retained so app.js and its existing paths stay unchanged.
class DoughnutChart3D {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    this.overlay = document.getElementById("chart-center-overlay");
    this.onNavigate = options.onNavigate || (() => {});
    this.greenPct = 0;
    this.redPct = 0;
    this.selectedSlice = null;
    this.hoveredSlice = null;
    this.render();
  }

  polar(cx, cy, radius, angle) {
    return [cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius];
  }

  arcPath(start, end, outer = 132, inner = 78) {
    const cx = 210, cy = 180;
    const [sx, sy] = this.polar(cx, cy, outer, start);
    const [ex, ey] = this.polar(cx, cy, outer, end);
    const [isx, isy] = this.polar(cx, cy, inner, end);
    const [iex, iey] = this.polar(cx, cy, inner, start);
    const large = end - start > Math.PI ? 1 : 0;
    return `M ${sx} ${sy} A ${outer} ${outer} 0 ${large} 1 ${ex} ${ey} L ${isx} ${isy} A ${inner} ${inner} 0 ${large} 0 ${iex} ${iey} Z`;
  }

  updateData(greenPct, redPct) {
    this.greenPct = Math.max(0, Math.min(100, Number(greenPct) || 0));
    this.redPct = Math.max(0, Math.min(100, Number(redPct) || 0));
    this.selectedSlice = null;
    this.render();
  }

  render() {
    if (!this.container) return;
    const total = this.greenPct + this.redPct;
    const greenAngle = total > 0 ? (this.greenPct / total) * Math.PI * 2 : 0;
    const start = -Math.PI / 2;
    const gap = 0.018;
    const slices = [];

    if (this.greenPct > 0) {
      const end = start + greenAngle;
      slices.push({ type: "GREEN", pct: this.greenPct, mid: (start + end) / 2,
        d: this.arcPath(start + gap, end - gap) });
    }
    if (this.redPct > 0) {
      const end = start + Math.PI * 2;
      const redStart = start + greenAngle;
      slices.push({ type: "RED", pct: this.redPct, mid: (redStart + end) / 2,
        d: this.arcPath(redStart + gap, end - gap) });
    }

    const paths = slices.map(slice => `
      <path class="donut-slice ${slice.type.toLowerCase()}"
        data-type="${slice.type}" data-pct="${slice.pct}"
        data-mid="${slice.mid}" d="${slice.d}" tabindex="0"
        role="button" aria-label="${slice.type} records: ${slice.pct.toFixed(1)} percent">
      </path>`).join("");

    this.container.innerHTML = `
      <svg class="donut-svg" viewBox="0 0 420 360" role="img"
        aria-label="Data quality distribution: ${this.greenPct}% GREEN, ${this.redPct}% RED">
        <defs>
          <filter id="donut-shadow" x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow dx="0" dy="9" stdDeviation="9" flood-color="#000" flood-opacity=".35"/>
          </filter>
        </defs>
        <circle cx="210" cy="180" r="132" class="donut-track"/>
        <g filter="url(#donut-shadow)">${paths}</g>
      </svg>`;
    this.container.querySelectorAll(".donut-slice").forEach(path => {
      const activate = () => this.setHover(path);
      path.addEventListener("mouseenter", activate);
      // Keyboard focus only (not mouse clicks), so the card can't get stuck after a click
      path.addEventListener("focus", () => { if (path.matches(":focus-visible")) activate(); });
      path.addEventListener("mouseleave", () => { path.blur(); this.clearHover(); });
      path.addEventListener("blur", () => this.clearHover());
      path.addEventListener("click", () => {
        const type = path.dataset.type;
        this.selectedSlice = this.selectedSlice === type ? null : type;
        this.onNavigate(type);
      });
      path.addEventListener("dblclick", () => this.onNavigate(path.dataset.type));
      path.addEventListener("keydown", e => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          this.onNavigate(path.dataset.type);
        }
      });
    });
    this.clearHover();

    // Leaving the chart area at any point hides the card
    if (this.container && !this.container.dataset.hoverBound) {
      this.container.dataset.hoverBound = "1";
      this.container.addEventListener("mouseleave", () => this.clearHover());
    }
  }

  setHover(path) {
    this.clearHover();
    const type = path.dataset.type;
    const pct = Number(path.dataset.pct);
    const mid = Number(path.dataset.mid);
    path.classList.add("is-hovered");
    path.style.setProperty("--lift-x", `${Math.cos(mid) * 7}px`);
    path.style.setProperty("--lift-y", `${Math.sin(mid) * 7}px`);
    this.hoveredSlice = type;
    this.updateCenterOverlay(type, pct);
  }

  clearHover() {
    this.hoveredSlice = null;
    this.container?.querySelectorAll(".donut-slice").forEach(path => path.classList.remove("is-hovered"));
    this.hideFloatingStat();
  }

  // Correct Data % shown by default on the floating glass card
  // The card stays hidden until a slice is hovered (no default display)
  setDefaultStat(greenPct) {
    this.defaultPct = greenPct;
  }

  hideFloatingStat() {
    if (!this.overlay) return;
    this.overlay.style.opacity = "0";
    this.overlay.innerHTML = "";
  }

  updateCenterOverlay(type, pct) {
    this.renderFloatingStat(type, pct);
  }

  renderFloatingStat(type, pct) {
    if (!this.overlay) return;
    const correct = type === "GREEN";
    this.overlay.innerHTML = `
      <div class="float-stat ${correct ? "is-correct" : "is-action"}">
        <div class="float-stat-label">${correct ? "✓ Correct Data" : "⚠ Action Required!"}</div>
        <div class="float-stat-value">${Number(pct).toFixed(1)}%</div>
        <div class="float-stat-sub">${correct ? "requires no changes" : "click to review"}</div>
      </div>`;
    this.overlay.style.opacity = "1";
  }

  destroy() {
    if (this.container) this.container.innerHTML = "";
  }
}

window.DoughnutChart3D = DoughnutChart3D;
