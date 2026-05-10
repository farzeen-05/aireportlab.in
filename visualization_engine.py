"""
visualization_engine.py — memory-optimized for Render free tier (512MB)
"""

import os
import time
import warnings
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
import seaborn as sns
from collections import Counter

warnings.filterwarnings("ignore")
matplotlib.use("Agg")

# ─── Palette & Style ──────────────────────────────────────────────────────────
PALETTE    = "Set2"
ACCENT     = "#4C72B0"
ACCENT2    = "#DD8452"
BG         = "#F8F9FB"
GRID_COLOR = "#E0E3EA"
TEXT_COLOR = "#2B2D42"
FIG_DPI    = 72          # ← lowered from 130 — biggest single memory saving


def _style():
    sns.set_theme(style="whitegrid", palette=PALETTE, font_scale=1.0)
    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG,
        "axes.edgecolor": GRID_COLOR, "axes.labelcolor": TEXT_COLOR,
        "xtick.color": TEXT_COLOR, "ytick.color": TEXT_COLOR,
        "text.color": TEXT_COLOR, "grid.color": GRID_COLOR,
        "grid.linestyle": "--", "grid.alpha": 0.7,
        "font.family": "DejaVu Sans",
    })


def _save(fig, path):
    """Save figure and immediately free all its memory."""
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    plt.close('all')     # ← force-close any leaked figures


def _ts():
    return str(int(time.time() * 1000))[-6:]


# ─── Column Profiler ──────────────────────────────────────────────────────────

class ColumnProfiler:
    ID_PATTERNS       = ["id", "_id", "code", "number", "num", "no", "ref",
                         "ordernum", "order_id", "patient_id", "tweet_id",
                         "author_id", "order_number"]
    DATETIME_PATTERNS = ["date", "time", "at", "created", "timestamp",
                         "period", "year", "month", "day"]

    def __init__(self, df):
        self.df = df.copy()
        self.roles = {}
        self._profile()

    def _is_id(self, col):
        lc = col.lower()
        if any(p in lc for p in self.ID_PATTERNS):
            return True
        s = self.df[col]
        if pd.api.types.is_numeric_dtype(s):
            if s.nunique() == len(s) and s.nunique() > 50:
                return True
        return False

    def _is_datetime(self, col):
        lc = col.lower()
        if any(p in lc for p in self.DATETIME_PATTERNS):
            try:
                pd.to_datetime(self.df[col].dropna().head(20))
                return True
            except Exception:
                return False
        return False

    def _profile(self):
        for col in self.df.columns:
            s = self.df[col]
            if self._is_id(col):
                self.roles[col] = "id"
            elif self._is_datetime(col):
                self.roles[col] = "datetime"
            elif pd.api.types.is_numeric_dtype(s):
                n = s.nunique()
                if n == 2:
                    self.roles[col] = "binary"
                elif n <= 15 and n / max(len(s), 1) < 0.05:
                    self.roles[col] = "categorical"
                else:
                    self.roles[col] = "numeric"
            else:
                n   = s.nunique()
                avg = s.dropna().astype(str).str.len().mean()
                self.roles[col] = "text" if avg > 60 or n > 30 else "categorical"

    def by_role(self, *roles):
        return [c for c, r in self.roles.items() if r in roles]


# ─── Main Engine ──────────────────────────────────────────────────────────────

class VisualizationEngine:

    def __init__(self, output_dir="static/charts"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def run(self, df):
        _style()

        # ── Memory safety: cap dataset size ───────────────────────────────────
        if len(df) > 5000:
            df = df.sample(5000, random_state=42)
        if len(df.columns) > 20:
            df = df.iloc[:, :20]

        self.df      = df.copy()
        self.profiler = ColumnProfiler(df)
        self.charts  = {}

        # Run each section — limit counts to save memory
        self._numeric_distributions()
        self._categorical_distributions()
        self._datetime_trends()
        self._correlation_heatmap()
        self._binary_vs_numeric()
        self._binary_vs_categorical()
        self._pairwise_numeric()
        self._domain_specific()
        self._dataset_overview()

        plt.close('all')   # final cleanup
        return self.charts

    # ── 1. Numeric distributions (max 6 columns) ─────────────────────────────

    def _numeric_distributions(self):
        for col in self.profiler.by_role("numeric")[:6]:   # ← capped at 6
            s = self.df[col].dropna()
            if len(s) < 5:
                continue
            fig, axes = plt.subplots(1, 2, figsize=(10, 4))   # ← smaller fig
            sns.histplot(s, bins=25, kde=True, color=ACCENT,
                         line_kws={"lw": 2}, ax=axes[0])
            axes[0].set_title(f"{col} — Distribution", fontweight="bold")
            axes[0].set_xlabel(col)
            axes[1].boxplot(s, vert=False, patch_artist=True,
                            boxprops=dict(facecolor=ACCENT, alpha=0.6),
                            medianprops=dict(color=ACCENT2, lw=2),
                            whiskerprops=dict(color=TEXT_COLOR),
                            flierprops=dict(marker="o", color=ACCENT2,
                                            markersize=3, alpha=0.5))
            axes[1].set_title(f"{col} — Box Plot", fontweight="bold")
            axes[1].set_yticks([])
            path = os.path.join(self.output_dir, f"dist_{col}_{_ts()}.png")
            _save(fig, path)
            self.charts[f"dist_{col}"] = path

    # ── 2. Categorical distributions (max 6 columns) ─────────────────────────

    def _categorical_distributions(self):
        for col in self.profiler.by_role("categorical", "binary")[:6]:  # ← capped
            s  = self.df[col].dropna().astype(str)
            vc = s.value_counts().head(10)
            if vc.empty:
                continue
            if len(vc) <= 6:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
                ax1.pie(vc, labels=vc.index, autopct="%1.1f%%",
                        colors=sns.color_palette(PALETTE, len(vc)),
                        startangle=140,
                        wedgeprops=dict(edgecolor="white", linewidth=2))
                ax1.set_title(f"{col} — Composition", fontweight="bold")
                sns.barplot(x=vc.index, y=vc.values, palette=PALETTE, ax=ax2)
                ax2.set_title(f"{col} — Counts", fontweight="bold")
                ax2.tick_params(axis="x", rotation=20)
            else:
                fig, ax = plt.subplots(figsize=(9, 4))
                sns.barplot(x=vc.values, y=vc.index, palette=PALETTE,
                            ax=ax, orient="h")
                ax.set_title(f"{col} — Top Categories", fontweight="bold")
            path = os.path.join(self.output_dir, f"cat_{col}_{_ts()}.png")
            _save(fig, path)
            self.charts[f"cat_{col}"] = path

    # ── 3. Datetime trends (max 2 numeric cols) ───────────────────────────────

    def _datetime_trends(self):
        dt_cols  = self.profiler.by_role("datetime")
        num_cols = self.profiler.by_role("numeric")
        cat_cols = self.profiler.by_role("categorical")
        if not dt_cols:
            return
        dcol = dt_cols[0]
        temp = self.df.copy()
        temp[dcol] = pd.to_datetime(temp[dcol], errors="coerce")
        temp = temp.dropna(subset=[dcol])
        if temp.empty:
            return
        span = (temp[dcol].max() - temp[dcol].min()).days
        freq, label = ("ME","Month") if span > 730 else ("W","Week") if span > 60 else ("D","Day")

        for ncol in num_cols[:2]:    # ← capped at 2 (was 4)
            grp = temp.set_index(dcol)[ncol].resample(freq).mean().dropna()
            if len(grp) < 2:
                continue
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.fill_between(grp.index, grp.values, alpha=0.15, color=ACCENT)
            sns.lineplot(x=grp.index, y=grp.values, color=ACCENT, lw=2, ax=ax)
            ax.set_title(f"{ncol} — Trend over {label}", fontweight="bold")
            ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %Y"))
            ax.xaxis.set_major_locator(
                matplotlib.dates.AutoDateLocator(minticks=4, maxticks=8))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=25)
            path = os.path.join(self.output_dir, f"trend_{ncol}_{_ts()}.png")
            _save(fig, path)
            self.charts[f"trend_{ncol}"] = path

        if not num_cols and cat_cols:
            grp = temp.set_index(dcol).resample(freq).size()
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.fill_between(grp.index, grp.values, alpha=0.15, color=ACCENT2)
            sns.lineplot(x=grp.index, y=grp.values, color=ACCENT2, lw=2, ax=ax)
            ax.set_title(f"Event Count over {label}", fontweight="bold")
            path = os.path.join(self.output_dir, f"trend_events_{_ts()}.png")
            _save(fig, path)
            self.charts["trend_event_count"] = path

    # ── 4. Correlation heatmap ────────────────────────────────────────────────

    def _correlation_heatmap(self):
        num_cols = self.profiler.by_role("numeric", "binary")
        if len(num_cols) < 3:
            return
        num_cols = num_cols[:15]    # ← cap at 15 cols
        corr = self.df[num_cols].corr()
        size = max(7, len(num_cols))
        fig, ax = plt.subplots(figsize=(size, size - 1))
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="coolwarm",
                    center=0, linewidths=0.5, square=True, ax=ax,
                    annot_kws={"size": 8}, cbar_kws={"shrink": 0.8})
        ax.set_title("Feature Correlation Matrix", fontweight="bold", pad=12)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
        path = os.path.join(self.output_dir, f"correlation_{_ts()}.png")
        _save(fig, path)
        self.charts["correlation_heatmap"] = path

    # ── 5. Binary vs numeric (max 4 cols) ────────────────────────────────────

    def _binary_vs_numeric(self):
        bin_cols = self.profiler.by_role("binary")
        num_cols = self.profiler.by_role("numeric")
        if not bin_cols or not num_cols:
            return
        target = bin_cols[0]
        for i in range(0, len(num_cols[:4]), 2):    # ← capped at 4
            chunk = num_cols[i:i+2]
            fig, axes = plt.subplots(1, len(chunk), figsize=(6*len(chunk), 4))
            if len(chunk) == 1:
                axes = [axes]
            for ax, ncol in zip(axes, chunk):
                sns.violinplot(x=target, y=ncol, data=self.df,
                               palette=PALETTE, inner="box", ax=ax, cut=0)
                ax.set_title(f"{ncol} by {target}", fontweight="bold")
            path = os.path.join(self.output_dir,
                                f"violin_{target}_{i}_{_ts()}.png")
            _save(fig, path)
            self.charts[f"violin_{target}_{i}"] = path

    # ── 6. Binary vs categorical (max 3 cols) ────────────────────────────────

    def _binary_vs_categorical(self):
        bin_cols = self.profiler.by_role("binary")
        cat_cols = self.profiler.by_role("categorical")
        if not bin_cols or not cat_cols:
            return
        target = bin_cols[0]
        for ccol in cat_cols[:3]:    # ← capped at 3
            ct = pd.crosstab(self.df[ccol], self.df[target], normalize="index")
            if ct.empty:
                continue
            fig, ax = plt.subplots(figsize=(max(7, len(ct)*0.8), 4))
            ct.plot(kind="bar", stacked=True, colormap="Set2", ax=ax,
                    edgecolor="white", linewidth=0.5)
            ax.set_title(f"{ccol} → {target} (rate)", fontweight="bold")
            ax.tick_params(axis="x", rotation=30)
            ax.legend(title=target, bbox_to_anchor=(1.01, 1), loc="upper left")
            path = os.path.join(self.output_dir,
                                f"bar_{ccol}_vs_{target}_{_ts()}.png")
            _save(fig, path)
            self.charts[f"bar_{ccol}_vs_{target}"] = path

    # ── 7. Pairwise scatter (top 3 pairs) ────────────────────────────────────

    def _pairwise_numeric(self):
        num_cols = self.profiler.by_role("numeric")
        if len(num_cols) < 2:
            return
        corr = self.df[num_cols].corr().abs()
        mask = np.triu(np.ones(corr.shape), k=1).astype(bool)
        stacked = corr.where(mask).stack().sort_values(ascending=False)
        stacked = stacked[stacked.index.get_level_values(0) !=
                          stacked.index.get_level_values(1)].head(3)   # ← 3 (was 5)
        bin_col = (self.profiler.by_role("binary") or [None])[0]
        cat_col = (self.profiler.by_role("categorical") or [None])[0]
        hue_col = bin_col or cat_col
        for (c1, c2), _ in stacked.items():
            if c1 == c2:
                continue
            keep = list(dict.fromkeys([c1, c2] + ([hue_col] if hue_col else [])))
            keep = [k for k in keep if k in self.df.columns]
            hue_actual = hue_col if (hue_col and hue_col in keep) else None
            tmp = self.df[keep].copy()
            for col_ in tmp.select_dtypes(include=["string"]).columns:
                tmp[col_] = tmp[col_].astype(str)
            tmp = tmp.dropna()
            if len(tmp) < 10:
                continue
            fig, ax = plt.subplots(figsize=(6, 4))
            if hue_actual:
                sns.scatterplot(x=c1, y=c2, hue=hue_actual, data=tmp,
                                palette=PALETTE, alpha=0.6, s=30, ax=ax,
                                edgecolors="none")
                ax.legend(title=hue_actual, bbox_to_anchor=(1.01, 1),
                          loc="upper left", fontsize=8)
            else:
                sns.regplot(x=c1, y=c2, data=tmp,
                            scatter_kws={"alpha": 0.4, "s": 20},
                            line_kws={"color": ACCENT2, "lw": 2},
                            ax=ax, color=ACCENT)
            ax.set_title(f"{c1} vs {c2}", fontweight="bold")
            path = os.path.join(self.output_dir,
                                f"scatter_{c1}_{c2}_{_ts()}.png")
            _save(fig, path)
            self.charts[f"scatter_{c1}_vs_{c2}"] = path

    # ── 8. Domain-specific ────────────────────────────────────────────────────

    def _domain_specific(self):
        cl = {c.lower(): c for c in self.df.columns}
        if "stroke" in cl:
            self._healthcare_charts(cl)
        if "delivery_time_min" in cl or "distance_km" in cl:
            self._delivery_charts(cl)
        if "precipitation" in cl or "temp_max" in cl:
            self._weather_charts(cl)
        if "sales" in cl or "productline" in cl:
            self._sales_charts(cl)
        if "has_asthma" in cl or "asthma" in cl:
            self._asthma_charts(cl)
        text_like = [c for c in self.df.columns
                     if self.profiler.roles.get(c) == "text"
                     and self.df[c].str.len().mean() > 40]
        if text_like:
            self._nlp_charts(text_like)

    def _healthcare_charts(self, c):
        df = self.df
        for field, title in {
            "hypertension": "Stroke by Hypertension",
            "heart_disease": "Stroke by Heart Disease",
            "smoking_status": "Stroke by Smoking",
        }.items():    # ← reduced from 5 to 3
            if field in c:
                fig, ax = plt.subplots(figsize=(6, 4))
                sns.countplot(x=c[field], hue=c["stroke"], data=df,
                              palette="Set1", ax=ax, edgecolor="white")
                ax.set_title(title, fontweight="bold")
                ax.legend(title="Stroke")
                path = os.path.join(self.output_dir, f"health_{field}_{_ts()}.png")
                _save(fig, path)
                self.charts[f"health_{field}"] = path
        for cont in ["bmi", "avg_glucose_level"]:    # ← reduced from 3 to 2
            if cont in c:
                fig, ax = plt.subplots(figsize=(7, 4))
                sns.violinplot(x=c["stroke"], y=c[cont], data=df,
                               palette="Set1", inner="quartile", cut=0, ax=ax)
                ax.set_title(f"{cont.title()} by Stroke Status", fontweight="bold")
                path = os.path.join(self.output_dir, f"health_{cont}_{_ts()}.png")
                _save(fig, path)
                self.charts[f"health_{cont}_violin"] = path

    def _delivery_charts(self, c):
        df = self.df
        if "distance_km" in c and "delivery_time_min" in c:
            fig, ax = plt.subplots(figsize=(7, 4))
            hue = c.get("vehicle_type")
            sns.scatterplot(x=c["distance_km"], y=c["delivery_time_min"],
                            hue=hue, data=df, palette=PALETTE,
                            alpha=0.5, s=30, ax=ax, edgecolors="none")
            valid = df[[c["distance_km"], c["delivery_time_min"]]].dropna()
            m, b = np.polyfit(valid.iloc[:, 0], valid.iloc[:, 1], 1)
            xr = np.linspace(valid.iloc[:, 0].min(), valid.iloc[:, 0].max(), 100)
            ax.plot(xr, m*xr+b, "--", color=ACCENT2, lw=2)
            ax.set_title("Delivery Time vs Distance", fontweight="bold")
            if hue:
                ax.legend(title="Vehicle")
            path = os.path.join(self.output_dir, f"delivery_scatter_{_ts()}.png")
            _save(fig, path)
            self.charts["delivery_distance_vs_time"] = path
        if "traffic_level" in c and "delivery_time_min" in c:
            order = (df.groupby(c["traffic_level"])[c["delivery_time_min"]]
                     .median().sort_values().index.tolist())
            fig, ax = plt.subplots(figsize=(7, 4))
            sns.boxplot(x=c["traffic_level"], y=c["delivery_time_min"],
                        data=df, order=order, palette=PALETTE, ax=ax)
            ax.set_title("Delivery Time by Traffic Level", fontweight="bold")
            path = os.path.join(self.output_dir, f"delivery_traffic_{_ts()}.png")
            _save(fig, path)
            self.charts["delivery_by_traffic"] = path

    def _weather_charts(self, c):
        df = self.df.copy()
        if "date" in c:
            df[c["date"]] = pd.to_datetime(df[c["date"]], errors="coerce")
            df = df.set_index(c["date"]).sort_index()
            for col in ["temp_max", "precipitation"]:    # ← reduced from 4 to 2
                if col not in c:
                    continue
                monthly = df[c[col]].resample("ME").mean()
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.fill_between(monthly.index, monthly.values, alpha=0.2, color=ACCENT)
                sns.lineplot(x=monthly.index, y=monthly.values, color=ACCENT, lw=2, ax=ax)
                ax.set_title(f"Monthly {col.replace('_',' ').title()}", fontweight="bold")
                ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %Y"))
                path = os.path.join(self.output_dir, f"weather_{col}_{_ts()}.png")
                _save(fig, path)
                self.charts[f"weather_{col}"] = path

    def _sales_charts(self, c):
        df = self.df
        if "productline" in c and "sales" in c:
            grp = df.groupby(c["productline"])[c["sales"]].sum().sort_values(ascending=False)
            fig, ax = plt.subplots(figsize=(8, 4))
            bars = ax.bar(grp.index, grp.values,
                          color=sns.color_palette(PALETTE, len(grp)), edgecolor="white")
            ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=8)
            ax.set_title("Total Revenue by Product Line", fontweight="bold")
            ax.tick_params(axis="x", rotation=20)
            path = os.path.join(self.output_dir, f"sales_productline_{_ts()}.png")
            _save(fig, path)
            self.charts["sales_by_productline"] = path
        if "dealsize" in c:
            vc = df[c["dealsize"]].value_counts()
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.pie(vc, labels=vc.index, autopct="%1.1f%%",
                   colors=sns.color_palette(PALETTE, len(vc)),
                   startangle=140, wedgeprops=dict(edgecolor="white", lw=2))
            ax.set_title("Deal Size Distribution", fontweight="bold")
            path = os.path.join(self.output_dir, f"sales_dealsize_{_ts()}.png")
            _save(fig, path)
            self.charts["sales_deal_size"] = path

    def _asthma_charts(self, c):
        df = self.df
        target = c.get("has_asthma") or c.get("asthma_control_level")
        if not target:
            return
        for cont in ["bmi", "age"]:    # ← reduced from 5 to 2
            if cont in c:
                fig, ax = plt.subplots(figsize=(7, 4))
                sns.boxplot(x=target, y=c[cont], data=df, palette="Set2", ax=ax)
                ax.set_title(f"{c[cont]} by {target}", fontweight="bold")
                path = os.path.join(self.output_dir, f"asthma_{cont}_{_ts()}.png")
                _save(fig, path)
                self.charts[f"asthma_{cont}"] = path

    def _nlp_charts(self, text_cols):
        import re
        STOPWORDS = set("i me my we our you your he him his she her it its they them their what which who this that am is are was were be been being have has had do does did a an the and but if or because as until while of at by for with about against between into through during before after above below to from up down in out on off over under again further then once here there when where why how all both each few more most other some no nor not only own same so than too very s t can will just don should now".split())
        for tcol in text_cols[:1]:    # ← only 1 text column (was 2)
            s = self.df[tcol].dropna().astype(str)
            tokens = []
            for txt in s:
                tokens.extend(re.findall(r"\b[a-z]{4,}\b", txt.lower()))
            tokens = [t for t in tokens if t not in STOPWORDS]
            freq = Counter(tokens).most_common(15)    # ← 15 (was 20)
            if not freq:
                continue
            words, counts = zip(*freq)
            fig, ax = plt.subplots(figsize=(9, 4))
            colors = sns.color_palette("viridis", len(words))
            ax.barh(list(reversed(words)), list(reversed(counts)),
                    color=list(reversed(colors)))
            ax.set_title(f"Top Terms — {tcol}", fontweight="bold")
            path = os.path.join(self.output_dir, f"nlp_terms_{tcol}_{_ts()}.png")
            _save(fig, path)
            self.charts[f"nlp_terms_{tcol}"] = path

    # ── 9. Dataset overview ───────────────────────────────────────────────────

    def _dataset_overview(self):
        df = self.df
        n_rows, n_cols = df.shape
        missing_pct = df.isnull().mean() * 100
        role_counts = Counter(self.profiler.roles.values())

        fig = plt.figure(figsize=(12, 4))    # ← smaller (was 14x5)
        gs  = gridspec.GridSpec(1, 3, figure=fig, wspace=0.4)

        ax1 = fig.add_subplot(gs[0])
        miss = missing_pct[missing_pct > 0].sort_values(ascending=True)
        if miss.empty:
            ax1.text(0.5, 0.5, "No Missing Values ✓", ha="center", va="center",
                     fontsize=12, color="green", fontweight="bold")
            ax1.axis("off")
        else:
            ax1.barh(miss.index, miss.values,
                     color=[plt.cm.Reds(v/100) for v in miss.values])
            ax1.set_xlabel("% Missing")
            ax1.set_title("Missing Values", fontweight="bold")
            ax1.xaxis.set_major_formatter(mticker.PercentFormatter())

        ax2 = fig.add_subplot(gs[1])
        labels = list(role_counts.keys())
        sizes  = list(role_counts.values())
        ax2.pie(sizes, labels=labels, autopct="%1.0f%%",
                colors=sns.color_palette(PALETTE, len(labels)), startangle=90,
                wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2),
                textprops={"fontsize": 8})
        ax2.set_title("Column Types", fontweight="bold")

        ax3 = fig.add_subplot(gs[2])
        ax3.axis("off")
        summary = [
            ["Rows",        f"{n_rows:,}"],
            ["Columns",     f"{n_cols}"],
            ["Numeric",     str(role_counts.get("numeric", 0))],
            ["Categorical", str(role_counts.get("categorical", 0))],
            ["Binary",      str(role_counts.get("binary", 0))],
            ["Datetime",    str(role_counts.get("datetime", 0))],
            ["Missing cols",str((missing_pct > 0).sum())],
        ]
        table = ax3.table(cellText=summary, colLabels=["Metric", "Value"],
                          loc="center", cellLoc="left")
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.5)
        for (r, col_), cell in table.get_celld().items():
            if r == 0:
                cell.set_facecolor(ACCENT)
                cell.set_text_props(color="white", fontweight="bold")
            elif r % 2 == 0:
                cell.set_facecolor("#EEF0F5")
            cell.set_edgecolor(GRID_COLOR)
        ax3.set_title("Dataset Summary", fontweight="bold", pad=10)
        fig.suptitle("Dataset Overview", fontsize=14, fontweight="bold", y=1.02)

        path = os.path.join(self.output_dir, f"overview_{_ts()}.png")
        _save(fig, path)
        self.charts["dataset_overview"] = path
