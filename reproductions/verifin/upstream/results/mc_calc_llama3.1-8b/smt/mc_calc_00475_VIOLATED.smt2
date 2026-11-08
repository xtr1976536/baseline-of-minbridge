(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_property_plant_and_equipment_net_fy2023 Real)
(declare-const accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023 Real)
(declare-const property_plant_and_equipment_gross_fy2023 Real)

(assert (! (= property_plant_and_equipment_gross_fy2023 15524.0) :named evidence_property_plant_and_equipment_gross_fy2023))
(assert (! (= accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023 6076.0) :named evidence_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023))

(assert (! (= computed_property_plant_and_equipment_net_fy2023 (+ property_plant_and_equipment_gross_fy2023 (* -1 accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023))) :named formula_property_plant_and_equipment_net_fy2023))

(assert (! (or (> property_plant_and_equipment_gross_fy2023 0) (< property_plant_and_equipment_gross_fy2023 0)) :named denom_nonzero))
(assert (! (or (> accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023 0) (< accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023 0)) :named denom_accumulated_nonzero))

(assert (! (<= (- computed_property_plant_and_equipment_net_fy2023 9280.0) 92.8) :named claim_upper))
(assert (! (<= (- 9280.0 computed_property_plant_and_equipment_net_fy2023) 92.8) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2023_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2023_12_31_unit_USD_dims_none 9448) :named evidence_xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2023_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= property_plant_and_equipment_gross_fy2023 xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_property_plant_and_equipment_gross_fy2023_edgar_2023_12_31_0000097745_24_000007))
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2023_12_31_unit_USD_dims_none 15524) :named xbrl_instance_property_plant_and_equipment_gross_fy2023))
(assert (! (= accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023_edgar_2023_12_31_0000097745_24_000007))
(assert (! (= xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2023_12_31_unit_USD_dims_none 6076) :named xbrl_instance_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2023_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2023_12_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_19_606075268_PropertyPlantAndEquipmentNet_c_21_upper))
(assert (! (>= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2023_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2023_12_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_19_606075268_PropertyPlantAndEquipmentNet_c_21_lower))

(check-sat)
(get-unsat-core)
(get-model)