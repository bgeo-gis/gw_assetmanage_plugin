# Weighted Matrix Method

## Arc Information

- **`arc_id`:** Arc identifier.
- **`matcat_id`:** Material of the arc.
- **`arccat_id`:** Catalog identifier of the arc.
- **`dnom`:** Nominal diameter.

## Breaks per Year per Kilometer

- **`rleak`:** Breaks per year per kilometer.
- **`val_rleak`:** Min-max normalization of `rleak`.
- **`w1_rleak`:** Weight of `val_rleak` in the calculation of `val_1` (first iteration).
- **`w2_rleak`:** Weight of `val_rleak` in the calculation of `val_2` (second iteration).

## Failure Probability

- **`mleak`:** Failure probability of `matcat_id`, based on material configuration.
- **`val_mleak`:** Min-max normalization of `mleak`.
- **`w1_mleak`:** Weight of `val_mleak` in the calculation of `val_1` (first iteration).
- **`w2_mleak`:** Weight of `val_mleak` in the calculation of `val_2` (second iteration).

## Longevity

- **`calculated_builtdate`:** `builtdate` of the arc, or default `builtdate` for `matcat_id` if missing, based on material configuration.
- **`total_expected_useful_life`:** Expected useful life based on the configuration of materials. It calculates the maximum longevity for `matcat_id` if pressure is less than 50 meters, minimum longevity if it's more than 75 meters, and medium longevity otherwise.
- **`longevity`:** Remaining years of useful life, given by `calculated_builtdate` + `total_expected_useful_life` - current year.
- **`val_longevity`:** 10 minus the min-max normalization of `longevity`. Lower `longevity` values receive higher priority in replacement.
- **`w1_longevity`:** Weight of `val_longevity` in the calculation of `val_1` (first iteration).
- **`w2_longevity`:** Weight of `val_longevity` in the calculation of `val_2` (second iteration).

## Flow

- **`flow_avg`:** Average flow from Giswater. It's `0` if the value is missing.
- **`val_flow`:** Min-max normalization of `flow_avg`.
- **`w1_flow`:** Weight of `val_flow` in the calculation of `val_1` (first iteration).
- **`w2_flow`:** Weight of `val_flow` in the calculation of `val_2` (second iteration).

## Non-Revenue Water

- **`dma_id`:** DMA to which the arc belongs.
- **`nrw`:** Non-revenue water, in m³/km·day. Calculated by getting the volume of NRW and a period for `dma_id` from the table `dma_nrw` and dividing by the sum of lengths of arcs of that `dma_id`.
- **`val_nrw`:** `nrw` normalized as follows: 0 if `nrw` is less than 2, 10 if `nrw` is more than 20. For values between 2 and 20, `val_nrw` is scaled proportionally between 0 and 10.
- **`w1_nrw`:** Weight of `val_nrw` in the calculation of `val_1` (first iteration).
- **`w2_nrw`:** Weight of `val_nrw` in the calculation of `val_2` (second iteration).

## Compliance

- **`material_compliance`:** The level of compliance of `matcat_id`, ranging from 0 to 10.
- **`catalog_compliance`:** The level of compliance of `arccat_id`, ranging from 0 to 10.
- **`compliance`:** The compliance value of an arc is the lower of `material_compliance` or `catalog_compliance`.
- **`val_compliance`:** 10 - `compliance`. Lower `compliance` values receive higher priority in replacement.
- **`w1_compliance`:** Weight of `val_compliance` in the calculation of `val_1` (first iteration).
- **`w2_compliance`:** Weight of `val_compliance` in the calculation of `val_2` (second iteration).

## Strategic

- **`val_strategic`:** Indicates if an arc was evaluated as a strategic asset or not. A boolean value, 0 or 10.
- **`w1_strategic`:** Weight of `val_strategic` in the calculation of `val_1` (first iteration).
- **`w2_strategic`:** Weight of `val_strategic` in the calculation of `val_2` (second iteration).

## Mandatory

- **`mandatory`:** Mandatory arcs take precedence over others, ignoring any other parameters.

## Cost of Construction

- **`cost_by_meter`:** Replacement cost per meter of `arccat_id`, based on catalog configuration.
- **`length`:** Arc length in meters.
- **`cost_constr`:** `cost_by_meter` multiplied by `length`.

## Resulting Values

- **`val_1`:** Value of the first iteration, given by the sum of weighted values (`val_rleak`, `val_mleak`, `val_longevity`, `val_flow`, `val_nrw`, `val_strategic`, `val_compliance`) for the first iteration.
- **`val_2`:** Value of the second iteration, given by the sum of weighted values (`val_rleak`, `val_mleak`, `val_longevity`, `val_flow`, `val_nrw`, `val_strategic`, `val_compliance`) for the second iteration.
- **`cum_cost_constr`:** Cumulative cost of replacement.
- **`cum_length`:** Cumulative length of replaced pipes.
- **`replacement_year`:** Year of replacement, considering the yearly budget.
