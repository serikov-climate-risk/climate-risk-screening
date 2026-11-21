"""Rule-based adaptation finance tagging and a simplified Paris-alignment screen.

Tagging follows the three-step structure of the MDB-IDFC common principles for climate finance tracking
(adaptation): (1) a context-specific vulnerability statement, (2) an explicit intent to reduce that vulnerability,
(3) a clear and direct link between the financed activity and the vulnerability. The thresholds are screening
rules set in this study, not the rules of an institution. Every decision is recorded with the numbers that
triggered it.

The Paris-alignment screen is a simplified, rule-based check after the idea of the MDB joint approach for the
adaptation and resilience goal (assess the physical risk; where it is material, require resilience measures).
It is not the EBRD methodology.
"""
from __future__ import annotations

EXPOSED_DEPTH_RP100 = 0.10   # m: asset is exposed if the 1-in-100 flood depth is at least this
EXPOSED_DEPTH_RP500 = 0.50   # m: or the 1-in-500 depth is at least this
MATERIAL_EAD_SHARE = 0.0005  # share of asset value per year above which physical risk is material
RESIDUAL_OK_SHARE = 0.0005   # residual share after measures regarded as acceptable


def _base(row):
    return {"asset": row["asset"], "asset_class": row["asset_class"], "measure": row["measure"],
            "capex_meur": row["capex_meur"]}


def tag_measure(row: dict) -> dict:
    """row keys: asset, asset_class, measure, height_m, capex_meur, depth_rp100, depth_rp500, ead_share_base"""
    ctx = row["depth_rp100"] >= EXPOSED_DEPTH_RP100 or row["depth_rp500"] >= EXPOSED_DEPTH_RP500
    ctx_txt = (f"1-in-100 depth {row['depth_rp100']:.2f} m, 1-in-500 depth {row['depth_rp500']:.2f} m; "
               f"baseline expected annual damage {100 * row['ead_share_base']:.3f}% of value")
    if row["measure"] == "none":
        return {**_base(row), "context": ctx, "intent": False, "link": False, "tagged_capex_meur": 0.0,
                "decision": "no measure selected", "evidence": ctx_txt}
    intent = row["height_m"] > 0
    link = bool(row["height_m"] >= row["depth_rp100"] and ctx)
    if not ctx:
        dec = "not tagged: no context-specific vulnerability (asset not exposed at the screening thresholds)"
    elif not intent:
        dec = "not tagged: no explicit intent to reduce the flood vulnerability"
    elif not link:
        share = row["height_m"] / row["depth_rp100"] if row["depth_rp100"] > 0 else 0.0
        dec = (f"not tagged as stated: measure height {row['height_m']:.1f} m is below the 1-in-100 depth "
               f"{row['depth_rp100']:.2f} m, so the direct link to the vulnerability is only partial "
               f"(share {share:.0%} to be tagged after design confirmation)")
    else:
        dec = "tagged: vulnerability stated, intent explicit, measure height covers the 1-in-100 depth"
    tagged = row["capex_meur"] if (ctx and intent and link) else 0.0
    return {**_base(row), "context": ctx, "intent": intent, "link": link, "tagged_capex_meur": tagged,
            "decision": dec, "evidence": ctx_txt}


def paris_screen(ead_share_base: float, ead_share_residual: float, measure: str) -> str:
    if ead_share_base < MATERIAL_EAD_SHARE:
        return "aligned: physical flood risk not material at the screening threshold"
    if measure != "none" and ead_share_residual < RESIDUAL_OK_SHARE:
        return "aligned if the measure is in the project scope: residual flood risk below the threshold"
    if measure != "none":
        return "not yet aligned: measure selected but residual flood risk stays above the threshold"
    return "not aligned: material flood risk and no measure selected"
