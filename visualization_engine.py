"""
visualization_engine.py
=======================
Fully automatic visualization engine.
- Detects column types (numeric, categorical, datetime, text, binary/target, ID)
- Chooses the best chart for each column and column-pair
- Handles domain-specific datasets (healthcare, delivery, weather, sales, NLP)
- Mixes Matplotlib + Seaborn throughout
- Returns a dict: { chart_key: filepath }

Usage
-----
    from visualization_engine import VisualizationEngine
    engine = VisualizationEngine(output_dir="static/charts")
    chart_paths = engine.run(df)          # returns {label: path}
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
matplotlib.use("Agg")  # non-interactive backend

# ─── Palette & Style ────────────────────────────────────────────────────────
PALETTE      = "Set2"
ACCENT       = "#4C72B0"
ACCENT2      = "#DD8452"
BG           = "#F8F9FB"
GRID_COLOR   = "#E0E3EA"
TEXT_COLOR   = "#2B2D42"
FIG_DPI      = 130

def _style():
    """Apply a consistent, clean style before every figure."""
    sns.set_theme(style="whitegrid", palette=PALETTE, font_scale=1.05)
    plt.rcParams.update({
        "figure.facecolor":  BG,
        "axes.facecolor":    BG,
        "axes.edgecolor":    GRID_COLOR,
        "axes.labelcolor":   TEXT_COLOR,
        "xtick.color":       TEXT_COLOR,
        "ytick.color":       TEXT_COLOR,
        "text.color":        TEXT_COLOR,
        "grid.color":        GRID_COLOR,
        "grid.linestyle":    "--",
        "grid.alpha":        0.7,
        "font.family":       "DejaVu Sans",
    })

# ─── Helpers ────────────────────────────────────────────────────────────────

def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)


def _ts():
    return str(int(time.time() * 1000))[-6:]   # short unique suffix


# ─── Column-type detector ────────────────────────────────────────────────────

class ColumnProfiler:
    """
    Classifies every column into one or more roles:
        id | datetime | numeric | binary | categorical | text
    """

    ID_PATTERNS       = ["id", "_id", "code", "number", "num", "no", "ref",
                         "ordernum", "order_id", "patient_id", "tweet_id",
                         "author_id", "order_number"]
    DATETIME_PATTERNS = ["date", "time", "at", "created", "timestamp",
                         "period", "year", "month", "day"]

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.roles: dict[str, str] = {}
        self._profile()

    def _is_id(self, col: str) -> bool:
        lc = col.lower()
        if any(p in lc for p in self.ID_PATTERNS):
            return True
        s = self.df[col]
        if pd.api.types.is_numeric_dtype(s):
            # high cardinality integers that look sequential
            if s.nunique() == len(s) and s.nunique() > 50:
                return True
        return False

    def _is_datetime(self, col: str) -> bool:
        lc = col.lower()
        if any(p in lc for p in self.DATETIME_PATTERNS):
            s = self.df[col]
            try:
                pd.to_datetime(s.dropna().head(20), )
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
                n_unique = s.nunique()
                if n_unique == 2:
                    self.roles[col] = "binary"
                elif n_unique <= 15 and n_unique / max(len(s), 1) < 0.05:
                    self.roles[col] = "categorical"
                else:
                    self.roles[col] = "numeric"
            else:
                # object / string
                n_unique = s.nunique()
                avg_len = s.dropna().astype(str).str.len().mean()
                if avg_len > 60:
                    self.roles[col] = "text"
                elif n_unique <= 30:
                    self.roles[col] = "categorical"
                else:
                    self.roles[col] = "text"

    def by_role(self, *roles) -> list[str]:
        return [c for c, r in self.roles.items() if r in roles]


# ─── Main Engine ─────────────────────────────────────────────────────────────

class VisualizationEngine:
    """
    Auto-generates all meaningful charts for an arbitrary CSV dataset.
    Call  engine.run(df)  to get {label: filepath} dict.
    """

    def __init__(self, output_dir: str = "static/charts"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # ── public entry point ──────────────────────────────────────────────────

    def run(self, df: pd.DataFrame) -> dict[str, str]:
        _style()
        self.df = df.copy()
        self.profiler = ColumnProfiler(df)
        self.charts: dict[str, str] = {}

        self._numeric_distributions()
        self._categorical_distributions()
        self._datetime_trends()
        self._correlation_heatmap()
        self._binary_vs_numeric()
        self._binary_vs_categorical()
        self._pairwise_numeric()
        self._domain_specific()
        self._dataset_overview()

        return self.charts

    # ── 1. Numeric distributions ─────────────────────────────────────────────

    def _numeric_distributions(self):
        cols = self.profiler.by_role("numeric")
        if not cols:
            return

        for col in cols:
            s = self.df[col].dropna()
            if len(s) < 5:
                continue

            fig, axes = plt.subplots(1, 2, figsize=(12, 4))

            # Histogram + KDE
            ax = axes[0]
            sns.histplot(s, bins=30, kde=True, color=ACCENT,
                         line_kws={"lw": 2}, ax=ax)
            ax.set_title(f"{col} — Distribution", fontweight="bold")
            ax.set_xlabel(col)
            ax.set_ylabel("Count")

            # Box plot (horizontal)
            ax2 = axes[1]
            ax2.boxplot(s, vert=False, patch_artist=True,
                        boxprops=dict(facecolor=ACCENT, alpha=0.6),
                        medianprops=dict(color=ACCENT2, lw=2),
                        whiskerprops=dict(color=TEXT_COLOR),
                        flierprops=dict(marker="o", color=ACCENT2,
                                        markersize=4, alpha=0.5))
            ax2.set_title(f"{col} — Box Plot", fontweight="bold")
            ax2.set_xlabel(col)
            ax2.set_yticks([])

            path = os.path.join(self.output_dir,
                                f"dist_{col}_{_ts()}.png")
            _save(fig, path)
            self.charts[f"dist_{col}"] = path

    # ── 2. Categorical distributions ─────────────────────────────────────────

    def _categorical_distributions(self):
        cols = self.profiler.by_role("categorical", "binary")
        for col in cols:
            s = self.df[col].dropna().astype(str)
            vc = s.value_counts().head(12)
            if vc.empty:
                continue

            n_cat = len(vc)

            if n_cat <= 6:
                # Pie chart + bar side-by-side
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

                wedge_colors = sns.color_palette(PALETTE, n_cat)
                ax1.pie(vc, labels=vc.index, autopct="%1.1f%%",
                        colors=wedge_colors, startangle=140,
                        wedgeprops=dict(edgecolor="white", linewidth=2))
                ax1.set_title(f"{col} — Composition", fontweight="bold")

                sns.barplot(x=vc.index, y=vc.values, palette=PALETTE, ax=ax2)
                ax2.set_title(f"{col} — Counts", fontweight="bold")
                ax2.set_xlabel(col)
                ax2.set_ylabel("Count")
                ax2.tick_params(axis="x", rotation=20)
            else:
                fig, ax = plt.subplots(figsize=(10, 5))
                sns.barplot(x=vc.values, y=vc.index,
                            palette=PALETTE, ax=ax, orient="h")
                ax.set_title(f"{col} — Top Categories", fontweight="bold")
                ax.set_xlabel("Count")
                ax.set_ylabel(col)

            path = os.path.join(self.output_dir,
                                f"cat_{col}_{_ts()}.png")
            _save(fig, path)
            self.charts[f"cat_{col}"] = path

    # ── 3. Datetime trends ───────────────────────────────────────────────────

    def _datetime_trends(self):
        dt_cols  = self.profiler.by_role("datetime")
        num_cols = self.profiler.by_role("numeric")
        cat_cols = self.profiler.by_role("categorical")

        if not dt_cols:
            return

        dcol = dt_cols[0]
        temp = self.df.copy()
        temp[dcol] = pd.to_datetime(temp[dcol], 
                                     errors="coerce")
        temp = temp.dropna(subset=[dcol])
        if temp.empty:
            return

        # Infer best time granularity
        span_days = (temp[dcol].max() - temp[dcol].min()).days
        if span_days > 365 * 2:
            freq, label = "ME", "Month"
        elif span_days > 60:
            freq, label = "W", "Week"
        else:
            freq, label = "D", "Day"

        # Trend for each numeric column (up to 4)
        for ncol in num_cols[:4]:
            grp = (temp.set_index(dcol)[ncol]
                   .resample(freq).mean()
                   .dropna())
            if len(grp) < 2:
                continue

            fig, ax = plt.subplots(figsize=(12, 4))
            ax.fill_between(grp.index, grp.values, alpha=0.15, color=ACCENT)
            sns.lineplot(x=grp.index, y=grp.values,
                         color=ACCENT, lw=2.5, ax=ax)
            ax.set_title(f"{ncol} — Trend over {label}",
                         fontweight="bold")
            ax.set_xlabel(label)
            ax.set_ylabel(f"Mean {ncol}")
            ax.xaxis.set_major_formatter(
                matplotlib.dates.DateFormatter("%b %Y"))
            ax.xaxis.set_major_locator(
                matplotlib.dates.AutoDateLocator(minticks=4, maxticks=10))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=25)

            path = os.path.join(self.output_dir,
                                f"trend_{ncol}_{_ts()}.png")
            _save(fig, path)
            self.charts[f"trend_{ncol}"] = path

        # Event count over time (if mostly categorical data)
        if not num_cols and cat_cols:
            grp = temp.set_index(dcol).resample(freq).size()
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.fill_between(grp.index, grp.values, alpha=0.15, color=ACCENT2)
            sns.lineplot(x=grp.index, y=grp.values, color=ACCENT2,
                         lw=2.5, ax=ax)
            ax.set_title(f"Event Count over {label}", fontweight="bold")
            ax.set_xlabel(label)
            ax.set_ylabel("Count")
            path = os.path.join(self.output_dir,
                                f"trend_events_{_ts()}.png")
            _save(fig, path)
            self.charts["trend_event_count"] = path

        # Severity/numeric heatmap by year-month (geopolitical-style)
        sev_cols = [c for c in num_cols
                    if "sever" in c.lower() or "score" in c.lower()
                    or "level" in c.lower()]
        if sev_cols:
            scol = sev_cols[0]
            pivot = (temp.assign(Year=temp[dcol].dt.year,
                                  Month=temp[dcol].dt.month)
                     .groupby(["Year", "Month"])[scol].mean()
                     .unstack(fill_value=0))
            if pivot.shape[1] > 1:
                fig, ax = plt.subplots(figsize=(14, max(3, len(pivot) * 0.5)))
                sns.heatmap(pivot, cmap="YlOrRd", annot=True, fmt=".1f",
                            linewidths=0.5, ax=ax,
                            cbar_kws={"label": f"Mean {scol}"})
                ax.set_title(f"{scol} Heatmap by Year × Month",
                             fontweight="bold")
                path = os.path.join(self.output_dir,
                                    f"heatmap_temporal_{_ts()}.png")
                _save(fig, path)
                self.charts["heatmap_temporal"] = path

    # ── 4. Correlation heatmap ───────────────────────────────────────────────

    def _correlation_heatmap(self):
        num_cols = self.profiler.by_role("numeric", "binary")
        if len(num_cols) < 3:
            return

        corr = self.df[num_cols].corr()

        fig, ax = plt.subplots(figsize=(max(7, len(num_cols)), 
                                         max(5, len(num_cols) - 1)))
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, annot=True, fmt=".2f",
                    cmap="coolwarm", center=0, linewidths=0.5,
                    square=True, ax=ax,
                    annot_kws={"size": 9},
                    cbar_kws={"shrink": 0.8})
        ax.set_title("Feature Correlation Matrix", fontweight="bold", pad=12)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")

        path = os.path.join(self.output_dir, f"correlation_{_ts()}.png")
        _save(fig, path)
        self.charts["correlation_heatmap"] = path

    # ── 5. Binary target vs numeric (violin + box) ──────────────────────────

    def _binary_vs_numeric(self):
        bin_cols = self.profiler.by_role("binary")
        num_cols = self.profiler.by_role("numeric")
        if not bin_cols or not num_cols:
            return

        target = bin_cols[0]

        # Up to 6 numeric columns per chart grid
        for i in range(0, len(num_cols[:6]), 2):
            chunk = num_cols[i:i+2]
            fig, axes = plt.subplots(1, len(chunk),
                                     figsize=(6 * len(chunk), 5))
            if len(chunk) == 1:
                axes = [axes]
            for ax, ncol in zip(axes, chunk):
                sns.violinplot(x=target, y=ncol, data=self.df,
                               palette=PALETTE, inner="box", ax=ax,
                               cut=0)
                ax.set_title(f"{ncol} by {target}", fontweight="bold")
                ax.set_xlabel(target)
                ax.set_ylabel(ncol)

            path = os.path.join(self.output_dir,
                                f"violin_{target}_{i}_{_ts()}.png")
            _save(fig, path)
            self.charts[f"violin_{target}_{i}"] = path

    # ── 6. Binary target vs categorical (stacked / grouped bars) ───────────

    def _binary_vs_categorical(self):
        bin_cols = self.profiler.by_role("binary")
        cat_cols = self.profiler.by_role("categorical")
        if not bin_cols or not cat_cols:
            return

        target = bin_cols[0]
        for ccol in cat_cols[:4]:
            ct = pd.crosstab(self.df[ccol], self.df[target], normalize="index")
            if ct.empty:
                continue

            fig, ax = plt.subplots(figsize=(max(7, len(ct) * 0.8), 5))
            ct.plot(kind="bar", stacked=True,
                    colormap="Set2", ax=ax, edgecolor="white", linewidth=0.5)
            ax.set_title(f"{ccol} → {target} (rate)", fontweight="bold")
            ax.set_xlabel(ccol)
            ax.set_ylabel("Proportion")
            ax.tick_params(axis="x", rotation=30)
            ax.legend(title=target, bbox_to_anchor=(1.01, 1), loc="upper left")

            path = os.path.join(self.output_dir,
                                f"bar_{ccol}_vs_{target}_{_ts()}.png")
            _save(fig, path)
            self.charts[f"bar_{ccol}_vs_{target}"] = path

    # ── 7. Pairwise scatter (top correlated pairs) ──────────────────────────

    def _pairwise_numeric(self):
        num_cols = self.profiler.by_role("numeric")
        if len(num_cols) < 2:
            return

        # Find top-5 most correlated pairs (by |r|), strict upper-triangle only
        corr = self.df[num_cols].corr().abs()
        mask = np.triu(np.ones(corr.shape), k=1).astype(bool)
        stacked = corr.where(mask).stack().sort_values(ascending=False)
        # Drop any self-pairs
        stacked = stacked[stacked.index.get_level_values(0) !=
                          stacked.index.get_level_values(1)].head(5)
        pairs = stacked

        bin_col = (self.profiler.by_role("binary") or [None])[0]
        cat_col = (self.profiler.by_role("categorical") or [None])[0]
        hue_col = bin_col or cat_col

        for (c1, c2), _ in pairs.items():
            if c1 == c2:
                continue
            keep = list(dict.fromkeys([c1, c2] + ([hue_col] if hue_col else [])))
            keep = [k for k in keep if k in self.df.columns]
            hue_actual = hue_col if (hue_col and hue_col in keep) else None
            tmp = self.df[keep].copy()
            # Convert ArrowDtype / StringDtype to plain object for seaborn
            for col_ in tmp.select_dtypes(include=["string"]).columns:
                tmp[col_] = tmp[col_].astype(str)
            tmp = tmp.dropna()
            if len(tmp) < 10:
                continue

            fig, ax = plt.subplots(figsize=(7, 5))
            if hue_actual:
                sns.scatterplot(x=c1, y=c2, hue=hue_actual, data=tmp,
                                palette=PALETTE, alpha=0.65, s=40, ax=ax,
                                edgecolors="none")
                ax.legend(title=hue_actual, bbox_to_anchor=(1.01, 1),
                          loc="upper left", fontsize=9)
            else:
                sns.regplot(x=c1, y=c2, data=tmp, scatter_kws={"alpha": 0.4,
                            "s": 30}, line_kws={"color": ACCENT2, "lw": 2},
                            ax=ax, color=ACCENT)
            ax.set_title(f"{c1} vs {c2}", fontweight="bold")

            path = os.path.join(self.output_dir,
                                f"scatter_{c1}_{c2}_{_ts()}.png")
            _save(fig, path)
            self.charts[f"scatter_{c1}_vs_{c2}"] = path

    # ── 8. Domain-specific charts ────────────────────────────────────────────

    def _domain_specific(self):
        cols_lower = {c.lower(): c for c in self.df.columns}

        # ── Healthcare / Stroke ──────────────────────────────────────────────
        if "stroke" in cols_lower:
            self._healthcare_charts(cols_lower)

        # ── Food Delivery ────────────────────────────────────────────────────
        if "delivery_time_min" in cols_lower or "distance_km" in cols_lower:
            self._delivery_charts(cols_lower)

        # ── Weather ──────────────────────────────────────────────────────────
        if "precipitation" in cols_lower or "temp_max" in cols_lower:
            self._weather_charts(cols_lower)

        # ── Sales ────────────────────────────────────────────────────────────
        if "sales" in cols_lower or "productline" in cols_lower:
            self._sales_charts(cols_lower)

        # ── Asthma / General medical ─────────────────────────────────────────
        if "has_asthma" in cols_lower or "asthma" in cols_lower:
            self._asthma_charts(cols_lower)

        # ── NLP / Text classification ─────────────────────────────────────────
        text_like = [c for c in self.df.columns
                     if self.profiler.roles.get(c) == "text"
                     and self.df[c].str.len().mean() > 40]
        if text_like:
            self._nlp_charts(text_like)

    def _healthcare_charts(self, cols_lower):
        c = cols_lower
        df = self.df

        companions = {
            "hypertension": "Stroke by Hypertension",
            "heart_disease": "Stroke by Heart Disease",
            "smoking_status": "Stroke by Smoking Status",
            "work_type":      "Stroke by Work Type",
            "ever_married":   "Stroke by Marital Status",
        }
        for field, title in companions.items():
            if field in c:
                fig, ax = plt.subplots(figsize=(7, 4))
                sns.countplot(x=c[field], hue=c["stroke"],
                              data=df, palette="Set1", ax=ax,
                              edgecolor="white", linewidth=0.5)
                ax.set_title(title, fontweight="bold")
                ax.legend(title="Stroke")
                path = os.path.join(self.output_dir,
                                    f"health_{field}_{_ts()}.png")
                _save(fig, path)
                self.charts[f"health_{field}"] = path

        for cont in ["bmi", "avg_glucose_level", "age"]:
            if cont in c:
                fig, ax = plt.subplots(figsize=(8, 5))
                sns.violinplot(x=c["stroke"], y=c[cont], data=df,
                               palette="Set1", inner="quartile",
                               cut=0, ax=ax)
                ax.set_title(f"{cont.title()} by Stroke Status",
                             fontweight="bold")
                path = os.path.join(self.output_dir,
                                    f"health_{cont}_{_ts()}.png")
                _save(fig, path)
                self.charts[f"health_{cont}_violin"] = path

    def _delivery_charts(self, cols_lower):
        c = cols_lower
        df = self.df

        # Distance vs delivery time scatter coloured by vehicle
        if "distance_km" in c and "delivery_time_min" in c:
            fig, ax = plt.subplots(figsize=(8, 5))
            hue = c.get("vehicle_type")
            sns.scatterplot(x=c["distance_km"], y=c["delivery_time_min"],
                            hue=hue, data=df, palette=PALETTE,
                            alpha=0.6, s=50, ax=ax, edgecolors="none")
            # regression line
            valid = df[[c["distance_km"], c["delivery_time_min"]]].dropna()
            m, b = np.polyfit(valid.iloc[:, 0], valid.iloc[:, 1], 1)
            xr = np.linspace(valid.iloc[:, 0].min(), valid.iloc[:, 0].max(), 100)
            ax.plot(xr, m * xr + b, "--", color=ACCENT2, lw=2)
            ax.set_title("Delivery Time vs Distance", fontweight="bold")
            ax.set_xlabel("Distance (km)")
            ax.set_ylabel("Delivery Time (min)")
            if hue:
                ax.legend(title="Vehicle")
            path = os.path.join(self.output_dir,
                                f"delivery_scatter_{_ts()}.png")
            _save(fig, path)
            self.charts["delivery_distance_vs_time"] = path

        # Delivery time by traffic level (box)
        if "traffic_level" in c and "delivery_time_min" in c:
            order = (df.groupby(c["traffic_level"])[c["delivery_time_min"]]
                     .median().sort_values().index.tolist())
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.boxplot(x=c["traffic_level"], y=c["delivery_time_min"],
                        data=df, order=order, palette=PALETTE, ax=ax)
            ax.set_title("Delivery Time by Traffic Level", fontweight="bold")
            path = os.path.join(self.output_dir,
                                f"delivery_traffic_{_ts()}.png")
            _save(fig, path)
            self.charts["delivery_by_traffic"] = path

        # Mean delivery time by weather (bar)
        if "weather" in c and "delivery_time_min" in c:
            grp = (df.groupby(c["weather"])[c["delivery_time_min"]]
                   .mean().sort_values(ascending=False))
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.barplot(x=grp.index, y=grp.values,
                        palette="coolwarm", ax=ax)
            ax.set_title("Mean Delivery Time by Weather", fontweight="bold")
            ax.set_ylabel("Mean Delivery Time (min)")
            ax.tick_params(axis="x", rotation=20)
            path = os.path.join(self.output_dir,
                                f"delivery_weather_{_ts()}.png")
            _save(fig, path)
            self.charts["delivery_by_weather"] = path

    def _weather_charts(self, cols_lower):
        c = cols_lower
        df = self.df.copy()

        if "date" in c:
            df[c["date"]] = pd.to_datetime(df[c["date"]], errors="coerce")
            df = df.set_index(c["date"]).sort_index()

            for col in ["temp_max", "temp_min", "precipitation", "wind"]:
                if col not in c:
                    continue
                monthly = df[c[col]].resample("ME").mean()
                fig, ax = plt.subplots(figsize=(12, 4))
                ax.fill_between(monthly.index, monthly.values,
                                alpha=0.2, color=ACCENT)
                sns.lineplot(x=monthly.index, y=monthly.values,
                             color=ACCENT, lw=2, ax=ax)
                ax.set_title(f"Monthly Mean {col.replace('_', ' ').title()}",
                             fontweight="bold")
                ax.xaxis.set_major_formatter(
                    matplotlib.dates.DateFormatter("%b %Y"))
                path = os.path.join(self.output_dir,
                                    f"weather_{col}_{_ts()}.png")
                _save(fig, path)
                self.charts[f"weather_{col}"] = path

        if "weather" in c:
            vc = df[c["weather"]].value_counts()
            fig, ax = plt.subplots(figsize=(7, 4))
            sns.barplot(x=vc.index, y=vc.values, palette="Blues_d", ax=ax)
            ax.set_title("Weather Type Frequency", fontweight="bold")
            ax.tick_params(axis="x", rotation=20)
            path = os.path.join(self.output_dir,
                                f"weather_types_{_ts()}.png")
            _save(fig, path)
            self.charts["weather_types"] = path

        # Temp range band
        if "temp_max" in c and "temp_min" in c:
            if isinstance(df.index, pd.DatetimeIndex):
                monthly_max = df[c["temp_max"]].resample("ME").mean()
                monthly_min = df[c["temp_min"]].resample("ME").mean()
                fig, ax = plt.subplots(figsize=(12, 4))
                ax.fill_between(monthly_max.index, monthly_min.values,
                                monthly_max.values, alpha=0.3, color=ACCENT2,
                                label="Temp range")
                ax.plot(monthly_max.index, monthly_max.values,
                        color=ACCENT2, lw=1.5, label="Max")
                ax.plot(monthly_min.index, monthly_min.values,
                        color=ACCENT, lw=1.5, label="Min")
                ax.set_title("Monthly Temperature Range",
                             fontweight="bold")
                ax.legend()
                path = os.path.join(self.output_dir,
                                    f"temp_range_{_ts()}.png")
                _save(fig, path)
                self.charts["temp_range"] = path

    def _sales_charts(self, cols_lower):
        c = cols_lower
        df = self.df

        # Revenue by product line
        if "productline" in c and "sales" in c:
            grp = (df.groupby(c["productline"])[c["sales"]]
                   .sum().sort_values(ascending=False))
            fig, ax = plt.subplots(figsize=(9, 5))
            bars = ax.bar(grp.index, grp.values,
                          color=sns.color_palette(PALETTE, len(grp)),
                          edgecolor="white", linewidth=0.5)
            ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=9)
            ax.set_title("Total Revenue by Product Line", fontweight="bold")
            ax.set_ylabel("Total Sales")
            ax.tick_params(axis="x", rotation=20)
            path = os.path.join(self.output_dir,
                                f"sales_productline_{_ts()}.png")
            _save(fig, path)
            self.charts["sales_by_productline"] = path

        # Monthly sales trend
        if "orderdate" in c and "sales" in c:
            tmp = df.copy()
            tmp[c["orderdate"]] = pd.to_datetime(
                tmp[c["orderdate"]], errors="coerce")
            monthly = (tmp.set_index(c["orderdate"])[c["sales"]]
                       .resample("ME").sum().dropna())
            if not monthly.empty:
                fig, ax = plt.subplots(figsize=(12, 4))
                ax.fill_between(monthly.index, monthly.values,
                                alpha=0.15, color=ACCENT)
                sns.lineplot(x=monthly.index, y=monthly.values,
                             color=ACCENT, lw=2.5, ax=ax, marker="o")
                ax.set_title("Monthly Sales Trend", fontweight="bold")
                ax.xaxis.set_major_formatter(
                    matplotlib.dates.DateFormatter("%b %Y"))
                path = os.path.join(self.output_dir,
                                    f"sales_trend_{_ts()}.png")
                _save(fig, path)
                self.charts["sales_monthly_trend"] = path

        # Deal size pie
        if "dealsize" in c:
            vc = df[c["dealsize"]].value_counts()
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.pie(vc, labels=vc.index, autopct="%1.1f%%",
                   colors=sns.color_palette(PALETTE, len(vc)),
                   startangle=140, wedgeprops=dict(edgecolor="white", lw=2))
            ax.set_title("Deal Size Distribution", fontweight="bold")
            path = os.path.join(self.output_dir,
                                f"sales_dealsize_{_ts()}.png")
            _save(fig, path)
            self.charts["sales_deal_size"] = path

    def _asthma_charts(self, cols_lower):
        c = cols_lower
        df = self.df

        target = c.get("has_asthma") or c.get("asthma_control_level")
        if not target:
            return

        for cont in ["bmi", "age", "peak_expiratory_flow", "feno_level",
                     "number_of_er_visits"]:
            if cont in c:
                fig, ax = plt.subplots(figsize=(8, 4))
                sns.boxplot(x=target, y=c[cont], data=df,
                            palette="Set2", ax=ax)
                ax.set_title(f"{c[cont]} by {target}", fontweight="bold")
                path = os.path.join(self.output_dir,
                                    f"asthma_{cont}_{_ts()}.png")
                _save(fig, path)
                self.charts[f"asthma_{cont}"] = path

        for cat in ["smoking_status", "air_pollution_level",
                    "physical_activity_level", "gender"]:
            if cat in c:
                ct = pd.crosstab(df[c[cat]], df[target], normalize="index")
                fig, ax = plt.subplots(figsize=(8, 4))
                ct.plot(kind="bar", stacked=True, colormap="Set2", ax=ax,
                        edgecolor="white", linewidth=0.5)
                ax.set_title(f"{c[cat]} → {target}", fontweight="bold")
                ax.tick_params(axis="x", rotation=25)
                ax.legend(title=target, bbox_to_anchor=(1.01, 1),
                          loc="upper left")
                path = os.path.join(self.output_dir,
                                    f"asthma_{cat}_{_ts()}.png")
                _save(fig, path)
                self.charts[f"asthma_{cat}"] = path

    def _nlp_charts(self, text_cols):
        from collections import Counter
        import re

        STOPWORDS = set("""i me my myself we our ours ourselves you your yours
            yourself yourselves he him his himself she her hers herself it its
            itself they them their theirs themselves what which who whom this
            that these those am is are was were be been being have has had
            having do does did doing a an the and but if or because as until
            while of at by for with about against between into through during
            before after above below to from up down in out on off over under
            again further then once here there when where why how all both each
            few more most other some such no nor not only own same so than too
            very s t can will just don should now d ll m o re ve y ain aren
            couldn didn doesn hadn hasn haven isn ma mightn mustn needn shan
            shouldn wasn weren won wouldn""".split())

        cat_cols = self.profiler.by_role("categorical")

        for tcol in text_cols[:2]:
            s = self.df[tcol].dropna().astype(str)
            tokens = []
            for txt in s:
                tokens.extend(re.findall(r"\b[a-z]{4,}\b", txt.lower()))
            tokens = [t for t in tokens if t not in STOPWORDS]
            freq = Counter(tokens).most_common(20)
            if not freq:
                continue

            words, counts = zip(*freq)
            fig, ax = plt.subplots(figsize=(10, 5))
            colors = sns.color_palette("viridis", len(words))
            bars = ax.barh(list(reversed(words)),
                           list(reversed(counts)), color=list(reversed(colors)))
            ax.set_title(f"Top 20 Terms — {tcol}", fontweight="bold")
            ax.set_xlabel("Frequency")
            path = os.path.join(self.output_dir,
                                f"nlp_terms_{tcol}_{_ts()}.png")
            _save(fig, path)
            self.charts[f"nlp_terms_{tcol}"] = path

            # Label distribution if a categorical label col exists
            for lc in cat_cols:
                if lc in (tcol,):
                    continue
                lvc = self.df[lc].value_counts().head(10)
                fig, ax = plt.subplots(figsize=(8, 4))
                sns.barplot(x=lvc.values, y=lvc.index,
                            palette="rocket", ax=ax)
                ax.set_title(f"Label Distribution — {lc}", fontweight="bold")
                ax.set_xlabel("Count")
                path = os.path.join(self.output_dir,
                                    f"nlp_labels_{lc}_{_ts()}.png")
                _save(fig, path)
                self.charts[f"nlp_labels_{lc}"] = path
                break   # one label chart is enough

    # ── 9. Dataset overview card ─────────────────────────────────────────────

    def _dataset_overview(self):
        df = self.df
        roles = self.profiler.roles

        n_rows, n_cols = df.shape
        missing_pct = df.isnull().mean() * 100
        role_counts = Counter(roles.values())

        fig = plt.figure(figsize=(14, 5))
        gs = gridspec.GridSpec(1, 3, figure=fig, wspace=0.4)

        # Panel 1 — Missing value bar chart
        ax1 = fig.add_subplot(gs[0])
        miss = missing_pct[missing_pct > 0].sort_values(ascending=True)
        if miss.empty:
            ax1.text(0.5, 0.5, "No Missing Values ✓",
                     ha="center", va="center",
                     fontsize=13, color="green", fontweight="bold")
            ax1.axis("off")
        else:
            ax1.barh(miss.index, miss.values,
                     color=[plt.cm.Reds(v / 100) for v in miss.values])
            ax1.set_xlabel("% Missing")
            ax1.set_title("Missing Values", fontweight="bold")
            ax1.xaxis.set_major_formatter(mticker.PercentFormatter())

        # Panel 2 — Column role donut
        ax2 = fig.add_subplot(gs[1])
        labels = list(role_counts.keys())
        sizes  = list(role_counts.values())
        colors = sns.color_palette(PALETTE, len(labels))
        wedges, texts, autotexts = ax2.pie(
            sizes, labels=labels, autopct="%1.0f%%",
            colors=colors, startangle=90,
            wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2),
            textprops={"fontsize": 9})
        ax2.set_title("Column Types", fontweight="bold")

        # Panel 3 — Summary stats table
        ax3 = fig.add_subplot(gs[2])
        ax3.axis("off")
        summary = [
            ["Rows",        f"{n_rows:,}"],
            ["Columns",     f"{n_cols}"],
            ["Numeric",     str(role_counts.get("numeric", 0))],
            ["Categorical", str(role_counts.get("categorical", 0))],
            ["Binary",      str(role_counts.get("binary", 0))],
            ["Datetime",    str(role_counts.get("datetime", 0))],
            ["Text",        str(role_counts.get("text", 0))],
            ["ID cols",     str(role_counts.get("id", 0))],
            ["Missing cols",str((missing_pct > 0).sum())],
        ]
        table = ax3.table(cellText=summary,
                          colLabels=["Metric", "Value"],
                          loc="center", cellLoc="left")
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.6)
        for (r, col_), cell in table.get_celld().items():
            if r == 0:
                cell.set_facecolor(ACCENT)
                cell.set_text_props(color="white", fontweight="bold")
            elif r % 2 == 0:
                cell.set_facecolor("#EEF0F5")
            cell.set_edgecolor(GRID_COLOR)
        ax3.set_title("Dataset Summary", fontweight="bold", pad=10)

        fig.suptitle("Dataset Overview", fontsize=15,
                     fontweight="bold", y=1.02)

        path = os.path.join(self.output_dir, f"overview_{_ts()}.png")
        _save(fig, path)
        self.charts["dataset_overview"] = path
