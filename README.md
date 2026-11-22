# Climate risk screening of infrastructure assets: flood and heat exposure, adaptation finance tagging and a simplified Paris-alignment check

Research study on open data for 331 water, energy, transport and hospital assets around Belgrade, Serbia (about 20-21 E, 44.6-45.0 N). It shows how a physical climate risk screening of a project portfolio can be done with public hazard data, how adaptation measures are chosen when the climate scenario is uncertain, and how the chosen measures are tagged as adaptation finance and screened for alignment. Asset values, damage curves, measure costs and scenario factors are assumptions (listed in `data/sources.csv`); the study shows the method and the order of magnitude, never a valuation of real assets and never an institution's methodology.

## Question
How does an adaptation analyst screen an investment portfolio for physical climate risk, quantify the expected impact, tag adaptation finance and check alignment, using only open data?

## Main findings (assumed values and scenario factors, see limits)
| Result | Value |
|---|---|
| Assets in the table / excluded as in or on a river channel (1-in-10 depth at least 2 m, the 90 m grid cannot resolve them) | 331 / 23 (listed in `results/site_review_in_channel.csv`) |
| Assets screened, assumed replacement value | 308, 2,460 million EUR |
| Assets with 1-in-100 flood depth of at least 0.1 m | 18 |
| Expected annual flood loss, baseline / moderate / high (flood frequency x1.0 / x1.3 / x2.0) | 4.7 / 6.1 / 9.4 million EUR |
| Share of the baseline flood loss in transmission substations / water works / pumping stations | 48% / 20% / 16% |
| Days per year above 35 C at the ERA5 grid point: 1991-2020 baseline / moderate (SSP2-4.5, 2041-2060) / high (SSP5-8.5, 2041-2060), median of three CMIP6 models by the quantile delta method (range over the models 20.1 to 30.5 and 25.8 to 33.8) | 8.3 / 23.8 / 28.5 |
| Expected annual heat loss with the assumed loss rate, same scenarios (the earlier uniform +1.5 K and +3.0 K gave 8.5 and 13.7) | 4.4 / 12.6 / 15.1 million EUR |
| Minimax-regret plan | 17 of 308 assets get a measure (10 equipment elevation of 3 m, 5 flood walls of 1.5 m, 2 local barriers of 0.5 m), capital cost 15.1 million EUR |
| Net benefit of that plan, baseline / moderate / high | 3.05 / 4.34 / 7.35 million EUR per year |
| Maximum regret over the three scenarios, plan optimised for baseline / for high / minimax regret | 0.101 / 0.049 / 0.026 million EUR per year |
| Value of knowing the scenario (EVPI, equal weights) | 0.010 million EUR per year |
| Adaptation finance tagging | 11 of the 17 measures tagged (10.7 of 15.1 million EUR); 6 not tagged as stated because the measure is lower than the 1-in-100 depth |
| Paris-alignment screen (simplified) | 284 aligned (risk not material), 5 aligned if the measure is in scope, 12 not yet aligned, 7 not aligned (material risk and no measure pays) |

Reading of the results: the flood risk is concentrated in a few river-side assets (transmission substations, water works, pumping stations), so a screening that tags a handful of assets covers most of the loss; the scenario matters little for which measure is chosen (the EVPI is about 0.3% of the baseline net benefit of the plan) but the loss itself doubles in the high flood scenario and the heat loss triples; the seven assets that are not aligned are the ones where no measure of the three types pays for itself, which is the case for policy options other than hard protection (relocation, insurance, operating rules). A four-page screening note with these results and a policy-options section is in `docs/screening_note.pdf`.

## Method
1. **Assets.** Wastewater plants, water works, pumping stations, substations (transmission at 110 kV or more, distribution), power plants, rail and bus stations, hospitals and fuel storage from OpenStreetMap (`scripts/download_osm_assets.py`).
2. **Flood hazard.** Depth at the pixel containing each asset in the JRC / CEMS GloFAS river flood hazard maps (3 arc seconds, five return periods 10-500 years). A 3 x 3 pixel window maximum is a sensitivity: it doubles the portfolio loss (9.1 against 4.7 million EUR) because it picks up channel cells next to bank assets.
3. **Expected annual loss.** Depth-damage curve per asset class times assumed value, integrated over exceedance probability from the 1-in-500 flood (flat tail) to the 1-in-10 flood (no damage from more frequent mapped floods, a lower bound). Scenario stress factors multiply the flood frequency.
4. **Heat.** Days above 35 C from ERA5 daily maxima, shifted by the change of CMIP6 models (quantile delta method, `src/crscreen/cmip6.py`: for each model the change between its historical run 1995-2014 and its scenario run 2041-2060 per quantile of daily maximum temperature at the grid cell nearest to Belgrade is added to the ERA5 value of the same quantile, so hot days warm by their own amount), times an assumed loss fraction per day by asset class. Moderate is the median over the models of SSP2-4.5, high of SSP5-8.5 (`results/heat_days_cmip6.csv` lists every model).
5. **Adaptation measures.** Three measures that lower the effective flood depth by 0.5, 1.5 and 3 m, with costs as share of asset value, annualised at 6% over 30 years plus 1% operation. Net benefit per asset, scenario and measure; the plan per scenario, the minimax-regret plan, portfolio regret and EVPI (same logic as `gm-transit-climate-risk`).
6. **Tagging.** Rule-based, after the three-step structure of the MDB-IDFC common principles for climate finance tracking: context-specific vulnerability (1-in-100 depth of at least 0.1 m or 1-in-500 depth of at least 0.5 m), explicit intent, direct link (measure height at least the 1-in-100 depth). Each decision is stored with the numbers (`results/tagging_and_paris_screen.csv`).
7. **Paris-alignment screen.** Simplified rules in the structure of the idea of the MDB joint approach (risk not material, or material and a resilience measure brings the residual loss below 0.05% of value per year). It is not the methodology of any institution.


### Heat scenarios from CMIP6 (days above 35 C per year at the ERA5 grid point)
| Model | Scenario 2041-2060 | Own historical days above 35 C (1995-2014) | Mean warming of daily maximum (K) | ERA5 days after the quantile shift |
|---|---|---|---|---|
| ACCESS-CM2 | ssp245 | 0.4 | 3.16 | 30.5 |
| ACCESS-CM2 | ssp585 | 0.4 | 3.06 | 28.5 |
| AWI-CM-1-1-MR | ssp245 | 25.6 | 1.63 | 20.1 |
| AWI-CM-1-1-MR | ssp585 | 25.6 | 2.27 | 25.8 |
| BCC-CSM2-MR | ssp245 | 16.2 | 1.90 | 23.8 |
| BCC-CSM2-MR | ssp585 | 16.2 | 2.95 | 33.8 |

ERA5 1991-2020 has 8.3 days. The models differ strongly in their own historical hot days (0.4 to 25.6 per year at the nearest cell), which is why the shift is applied to ERA5 and not the model value taken as it is. Warming under SSP2-4.5 can exceed warming under SSP5-8.5 for one model (ACCESS-CM2: 3.16 and 3.06 K): one ensemble member and 20 years carry internal variability of that size, which is also why three models give a median, not a projection. The flood plans, the minimax-regret choice (17 assets) and the value of knowing the scenario (0.010 million EUR a year) do not change, because the adaptation measures in this screening act on flood only; the heat scenarios change the heat loss, which is the same for every plan.

## Data
| Data | Source | Licence |
|---|---|---|
| Flood depth | JRC / CEMS GloFAS global river flood hazard maps v2.1.2, tile ID134_N50_E20 | CC BY 4.0 |
| Assets | OpenStreetMap via Overpass, queried 21 Nov 2026 | ODbL |
| Temperature | ERA5 hourly 2 m temperature 1991-2020 at 44.75 N 20.5 E, Copernicus Climate Data Store | Copernicus licence |
| Climate change | CMIP6 daily maximum near-surface air temperature, historical 1995-2014 and SSP2-4.5 and SSP5-8.5 2041-2060 at the nearest cell, Pangeo CMIP6 cloud archive (`scripts/download_cmip6_pangeo.py`): ACCESS-CM2, AWI-CM-1-1-MR, BCC-CSM2-MR (BCC historical is member r2i1p1f1, its scenarios r1i1p1f1) | licence per model, not checked here |

Checksums of all raw files are in `data/manifest.csv`.

## Relation to the EBRD approach (read in the EBRD Sustainability Report 2023, chapter Paris alignment, 23 Nov 2026)
The report states that since the start of 2023 all new EBRD investment projects have been aligned with the Paris Agreement under the joint MDB framework of six building blocks (mitigation and adaptation alignment of investments, scaling climate finance, policy engagement, reporting, internal activities). For adaptation, the Bank ensures that the project or the counterparty has identified and addressed physical climate risks and that its activities do not undermine climate resilience in the operating context; projects needing a further assessment go through a three-step method: (1) potential material physical climate risks, (2) assessment of existing mitigants or inherent resilience, (3) whether there may be an impact on systemic climate resilience, with appropriate measures where risks or impacts are material. How the screen of this repository maps onto it:

| EBRD step | This repository | Covered |
|---|---|---|
| 1. Potential material physical climate risk | Exposure at the asset (1-in-100 depth of 0.1 m or 1-in-500 depth of 0.5 m) and expected annual loss above 0.05% of value (`tagging.paris_screen`) for flood; days above 35 C for heat at portfolio level | flood at asset level; heat only as a portfolio scenario |
| 2. Existing mitigants and inherent resilience | Residual loss after the selected measure below 0.05% of value (`aligned if the measure is in the project scope`) | flood only, thresholds set in this study |
| 3. Impact on systemic climate resilience | Not modelled: assets are screened one by one, without the network or the community they serve | no |

The thresholds are screening rules of this study, not those of the EBRD, whose methodology and thresholds were not read.

## Limits
- The values, depth-damage curves, measure costs, loss rate per hot day and scenario factors are assumptions. Flood frequency factors (1.3 and 2.0) are stress factors, not projections. The heat scenarios use three CMIP6 models, one member each and 20-year windows, one grid cell of 50 to 200 km near Belgrade; the median is not a probabilistic projection and the models differ by up to 10 days a year.
- The flood maps are riverine only (no surface water or coastal flooding), historical climate, 90 m resolution, with known artefacts in channels; 23 assets were excluded for that reason and need a site review.
- OpenStreetMap coverage and tags are incomplete; the asset set is a sample for the method, not an inventory of Belgrade.
- Below the 1-in-10 flood the damage is set to zero, so the flood loss is a lower bound. Heat loss is a single linear rate per class.
- The tagging and alignment rules are screening rules set in this study.

## Run
```
pip install -e .
python scripts/download_jrc_flood.py
python scripts/download_osm_assets.py
python scripts/download_era5_tmax.py      # needs a CDS account
python scripts/run_all.py
pytest
```
Results land in `results/`.
