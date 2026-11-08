(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_property_plant_and_equipment_net_fy2026 Real)
(declare-const accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2026 Real)
(declare-const property_plant_and_equipment_gross_fy2026 Real)

(assert (! (= accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2026 120338.0) :named evidence_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2026))
(assert (! (= property_plant_and_equipment_gross_fy2026 256421.0) :named evidence_property_plant_and_equipment_gross_fy2026))

(assert (! (= computed_property_plant_and_equipment_net_fy2026 (+ property_plant_and_equipment_gross_fy2026 (* -1 accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2026))) :named formula_property_plant_and_equipment_net_fy2026))

(assert (! (or (> property_plant_and_equipment_gross_fy2026 0) (< property_plant_and_equipment_gross_fy2026 0)) :named denom_nonzero))
(assert (! (or (> accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2026 0) (< accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2026 0)) :named denom_accumulated_nonzero))

(assert (! (<= (- computed_property_plant_and_equipment_net_fy2026 135983.0) 1359.83) :named claim_upper))
(assert (! (<= (- 135983.0 computed_property_plant_and_equipment_net_fy2026) 1359.83) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2026_01_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2026_01_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2026_01_31_unit_USD_dims_none 136083) :named evidence_xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2026_01_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= property_plant_and_equipment_gross_fy2026 xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_property_plant_and_equipment_gross_fy2026_edgar_2026_01_31_0000104169_26_000055))
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2026_01_31_unit_USD_dims_none 256421) :named xbrl_instance_property_plant_and_equipment_gross_fy2026))
(assert (! (= accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2026 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2026_01_31_unit_USD_dims_none) :named xbrl_bind_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2026_edgar_2026_01_31_0000104169_26_000055))
(assert (! (= xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2026_01_31_unit_USD_dims_none 120338) :named xbrl_instance_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2026))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2026_01_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2026_01_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_18_742652179_PropertyPlantAndEquipmentNet_c_16_upper))
(assert (! (>= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2026_01_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2026_01_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2026_01_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_18_742652179_PropertyPlantAndEquipmentNet_c_16_lower))

(check-sat)
(get-unsat-core)
(get-model)