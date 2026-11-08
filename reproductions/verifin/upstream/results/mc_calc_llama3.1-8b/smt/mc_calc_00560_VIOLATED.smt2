(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_property_plant_and_equipment_net_fy2025 Real)
(declare-const accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2025 Real)
(declare-const property_plant_and_equipment_gross_fy2025 Real)

(assert (! (= accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2025 4401.0) :named evidence_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2025))
(assert (! (= property_plant_and_equipment_gross_fy2025 10684.0) :named evidence_property_plant_and_equipment_gross_fy2025))

(assert (! (= computed_property_plant_and_equipment_net_fy2025 (- (* -1 accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2025) property_plant_and_equipment_gross_fy2025)) :named formula_property_plant_and_equipment_net_fy2025))

(assert (! (or (> property_plant_and_equipment_gross_fy2025 0) (< property_plant_and_equipment_gross_fy2025 0)) :named denom_nonzero))
(assert (! (or (> accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2025 0) (< accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2025 0)) :named denom_accumulated_nonzero))

(assert (! (<= (- computed_property_plant_and_equipment_net_fy2025 6283.0) 62.83) :named claim_upper))
(assert (! (<= (- 6283.0 computed_property_plant_and_equipment_net_fy2025) 62.83) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2025_01_26_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2025_01_26_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2025_01_26_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2025_01_26_unit_USD_dims_none 6283) :named evidence_xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2025_01_26_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= property_plant_and_equipment_gross_fy2025 xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2025_01_26_unit_USD_dims_none) :named xbrl_bind_property_plant_and_equipment_gross_fy2025_edgar_2025_01_26_0001045810_25_000023))
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2025_01_26_unit_USD_dims_none 10684) :named xbrl_instance_property_plant_and_equipment_gross_fy2025))
(assert (! (= accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2025 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2025_01_26_unit_USD_dims_none) :named xbrl_bind_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2025_edgar_2025_01_26_0001045810_25_000023))
(assert (! (= xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2025_01_26_unit_USD_dims_none 4401) :named xbrl_instance_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2025_01_26_unit_USD_dims_none (+ (* -1 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2025_01_26_unit_USD_dims_none) xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2025_01_26_unit_USD_dims_none)) 1.5) :named xbrl_calc_33_698507244_PropertyPlantAndEquipmentNet_c_13_upper))
(assert (! (>= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2025_01_26_unit_USD_dims_none (+ (* -1 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2025_01_26_unit_USD_dims_none) xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2025_01_26_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_33_698507244_PropertyPlantAndEquipmentNet_c_13_lower))

(check-sat)
(get-unsat-core)
(get-model)