(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_property_plant_and_equipment_net_fy2024 Real)
(declare-const accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2024 Real)
(declare-const property_plant_and_equipment_gross_fy2024 Real)

(assert (! (= accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2024 16483.0) :named evidence_accumulated_depreciation))
(assert (! (= property_plant_and_equipment_gross_fy2024 34876.0) :named evidence_property_plant))

(assert (! (= computed_property_plant_and_equipment_net_fy2024 (+ property_plant_and_equipment_gross_fy2024 (- accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2024))) :named formula_property_plant_and_equipment_net))

(assert (! (or (> accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2024 0) (< accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2024 0)) :named denom_nonzero))

(assert (! (<= (- computed_property_plant_and_equipment_net_fy2024 18593.0) 185.93) :named claim_upper))
(assert (! (<= (- 18593.0 computed_property_plant_and_equipment_net_fy2024) 185.93) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2024_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2024_12_31_unit_USD_dims_none 18393) :named evidence_xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2024_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= property_plant_and_equipment_gross_fy2024 xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_property_plant_and_equipment_gross_fy2024_edgar_2024_12_31_0000078003_25_000054))
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2024_12_31_unit_USD_dims_none 34876) :named xbrl_instance_property_plant_and_equipment_gross_fy2024))
(assert (! (= accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2024 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2024_edgar_2024_12_31_0000078003_25_000054))
(assert (! (= xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2024_12_31_unit_USD_dims_none 16483) :named xbrl_instance_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2024_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2024_12_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_70_549846612_PropertyPlantAndEquipmentNet_c_14_upper))
(assert (! (>= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2024_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2024_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2024_12_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_70_549846612_PropertyPlantAndEquipmentNet_c_14_lower))

(check-sat)
(get-unsat-core)
(get-model)