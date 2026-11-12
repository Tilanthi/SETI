"""JWST-like LRD subsample definition — pinned by JWSTLIKE_SPEC_v1.0 (Euclid DR1 LRD programme, Paper A+C).

Pure, deterministic functions that apply the pre-registered cuts to a table of frozen-selection outputs.
The SAME function is applied to real DR1 candidates and to injected (synthetic) rows; it never reads files.

Input columns (frozen selection v1.0.1 output names; injected rows carry the same names):
  sel_PHYS, sel_B25                     frozen chain finals (bool)
  CORE_PHYS, CORE_B25                   A1 robust core (sel ∧ SEL_TEMPLFIT ∧ P_SEL >= 0.5), from code/core
  z_PHYS, beta_uv_PHYS, beta_opt_PHYS, A_PHYS, MUV_PHYS     PHYS-photometry fit (primary chain)
  z, beta_uv, beta_opt, A, MUV          P1-photometry fit (B25 chain; secondary S4 only)
  HMAG_CORR                             corrected H magnitude (as used by dens.py / lf_dr1.py)
  MUMAX_MINUS_MAG                       MER VIS compactness
  LAYER                                 'WIDE' or 'DEEP' (added by caller)
optional (secondary variants only; NaN = not measured):
  beta_uv_TF, beta_opt_TF               PHYS fit on calibrated-TEMPLFIT NISP fluxes (BL tfcal refit, *_PHYS columns)
  K_HD, K_HD_ERR                        individual hot-dust ratio K_P (DEEP: IRAC2; WIDE: unWISE W2) and 1σ error

Output: boolean columns JL_PRIMARY and JL_S1..JL_S5, plus M5500_PHYS, ZBIN, MUVBIN, M5500BIN.
"""
import numpy as np
import pandas as pd

JL_VERSION = "1.0"

# ---- pre-registered constants (JWSTLIKE_SPEC_v1.0 §2) ----
BETA_OPT_MIN = 1.0        # rest-optical slope f_lambda ∝ lambda^beta: at least the median photometric JWST LRD (Kocevski+25 Table 3: 0.98)
BETA_UV_MAX = -0.6        # rest-UV slope: 98.8 % of Kocevski+25 LRDs are bluer; removes the galaxy/QSO pile-up at the -0.37 V-shape edge
Z_LO, Z_HI = 0.5, 2.1     # analysis window in z_fit (the chain already requires z_fit <= 2.1)
H_LIM = {"WIDE": 24.0, "DEEP": 25.0}   # HMAG_CORR limits (completeness-model domain)
# secondary variants
BETA_OPT_MIN_INCL = 0.55  # S1: 16th percentile of the JWST-LRD prism atlas through the frozen chain (PX-1 atlas_v1, Q1 noise)
MUMAX_PT = -2.75          # S2: point-like = within the DR1 stellar MUMAX_MINUS_MAG locus (95th percentile -2.75)
K_HD_SIG = 3.0            # S3: exclude an individually measured hot-dust ratio K_P > 1 at > 3 sigma
# bins
ZBINS = np.array([0.5, 1.0, 1.5, 2.1])
MUVBINS = np.arange(-25.0, -16.99, 1.0)
M5500BINS = np.arange(-26.0, -18.99, 1.0)
LAM_BREAK, LAM_5500 = 3645.0, 5500.0


def _distmod(z, H0=70.0, Om=0.27, OL=0.73):
    """Same flat cosmology as lrdlib.cosmo.PAPER (H0 70, Om 0.27); trapezoid on a fine grid."""
    z = np.asarray(z, float)
    zg = np.linspace(0, 10, 200001)
    Ez = np.sqrt(Om * (1 + zg) ** 3 + OL)
    dc = np.concatenate([[0], np.cumsum(0.5 * (1 / Ez[1:] + 1 / Ez[:-1]) * np.diff(zg))]) * 299792.458 / H0
    d = np.interp(np.clip(z, 1e-6, 10), zg, dc) * (1 + z)
    with np.errstate(divide="ignore", invalid="ignore"):
        return 5 * np.log10(d * 1e5)


def m5500(A, beta_opt, z):
    """Absolute AB magnitude of the fitted optical power law at rest 5500 A (same convention as lrdlib.fit.muv)."""
    A, b, z = (np.asarray(x, float) for x in (A, beta_opt, z))
    with np.errstate(divide="ignore", invalid="ignore"):
        m = 23.9 - 2.5 * np.log10(A) - 2.5 * (b + 2) * np.log10(LAM_5500 / LAM_BREAK)
    return m - _distmod(z) + 2.5 * np.log10(1 + z)


def _b(df, c):
    return df[c].fillna(False).astype(bool).to_numpy() if c in df else np.zeros(len(df), bool)


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def jl_flags(df: pd.DataFrame) -> pd.DataFrame:
    layer = df["LAYER"].to_numpy()
    hlim = np.where(layer == "DEEP", H_LIM["DEEP"], H_LIM["WIDE"])
    H = _f(df, "HMAG_CORR")
    z, bu, bo = _f(df, "z_PHYS"), _f(df, "beta_uv_PHYS"), _f(df, "beta_opt_PHYS")
    base = _b(df, "sel_PHYS") & _b(df, "CORE_PHYS") & (z >= Z_LO) & (z <= Z_HI) & (H <= hlim)
    beta = (bo >= BETA_OPT_MIN) & (bu <= BETA_UV_MAX)
    out = pd.DataFrame(index=df.index)
    out["JL_PRIMARY"] = base & beta
    out["JL_S1_INCL"] = base & (bo >= BETA_OPT_MIN_INCL) & (bu <= BETA_UV_MAX)
    out["JL_S2_PTLIKE"] = out["JL_PRIMARY"] & (_f(df, "MUMAX_MINUS_MAG") <= MUMAX_PT)
    k, ke = _f(df, "K_HD"), _f(df, "K_HD_ERR")
    hd = np.isfinite(k) & np.isfinite(ke) & (ke > 0) & ((k - 1.0) / np.where(ke > 0, ke, 1) > K_HD_SIG)
    out["JL_S3_NOHD"] = out["JL_PRIMARY"] & ~hd
    z1, bu1, bo1 = _f(df, "z"), _f(df, "beta_uv"), _f(df, "beta_opt")
    out["JL_S4_B25"] = (_b(df, "sel_B25") & _b(df, "CORE_B25") & (z1 >= Z_LO) & (z1 <= Z_HI) & (H <= hlim)
                        & (bo1 >= BETA_OPT_MIN) & (bu1 <= BETA_UV_MAX))
    out["JL_S5_TFBETA"] = out["JL_PRIMARY"] & (_f(df, "beta_opt_TF") >= BETA_OPT_MIN) & (_f(df, "beta_uv_TF") <= BETA_UV_MAX)
    out["M5500_PHYS"] = m5500(_f(df, "A_PHYS"), bo, z)
    zb = np.digitize(z, ZBINS) - 1                   # 0,1,2 inside; -1 / 3 outside
    zb[z == ZBINS[-1]] = len(ZBINS) - 2              # z_fit = 2.1 exactly belongs to the last bin
    out["ZBIN"] = zb
    out["MUVBIN"] = np.digitize(_f(df, "MUV_PHYS"), MUVBINS) - 1
    out["M5500BIN"] = np.digitize(out["M5500_PHYS"].to_numpy(), M5500BINS) - 1
    return out


def constants():
    return dict(JL_VERSION=JL_VERSION, BETA_OPT_MIN=BETA_OPT_MIN, BETA_UV_MAX=BETA_UV_MAX, Z_LO=Z_LO, Z_HI=Z_HI, H_LIM=H_LIM,
                BETA_OPT_MIN_INCL=BETA_OPT_MIN_INCL, MUMAX_PT=MUMAX_PT, K_HD_SIG=K_HD_SIG,
                ZBINS=ZBINS.tolist(), MUVBINS=MUVBINS.tolist(), M5500BINS=M5500BINS.tolist())


if __name__ == "__main__":
    import json
    print(json.dumps(constants(), indent=1))
