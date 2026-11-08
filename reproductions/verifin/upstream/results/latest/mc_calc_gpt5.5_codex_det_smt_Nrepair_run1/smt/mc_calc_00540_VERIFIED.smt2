(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_property_plant_and_equipment_net_fy2024 Real)
(declare-const accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2024 Real)
(declare-const property_plant_and_equipment_gross_fy2024 Real)

(assert (! (= accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2024 7783) :named evidence_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2024))
(assert (! (= property_plant_and_equipment_gross_fy2024 9873) :named evidence_property_plant_and_equipment_gross_fy2024))

(assert (! (= computed_property_plant_and_equipment_net_fy2024 (+ property_plant_and_equipment_gross_fy2024 (* (- 1) accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2024))) :named formula_property_plant_and_equipment_net_fy2024))

(assert (! (<= (- computed_property_plant_and_equipment_net_fy2024 2090) 2.0899999999999999) :named claim_upper))
(assert (! (<= (- 2090 computed_property_plant_and_equipment_net_fy2024) 2.0899999999999999) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2024_07_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2024_07_27_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2024_07_27_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2024_07_27_unit_USD_dims_none 2090) :named evidence_xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2024_07_27_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= property_plant_and_equipment_gross_fy2024 xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2024_07_27_unit_USD_dims_none) :named xbrl_bind_property_plant_and_equipment_gross_fy2024_edgar_2024_07_27_0000858877_24_000017))
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2024_07_27_unit_USD_dims_none 9873) :named xbrl_instance_property_plant_and_equipment_gross_fy2024))
(assert (! (= accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2024 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2024_07_27_unit_USD_dims_none) :named xbrl_bind_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2024_edgar_2024_07_27_0000858877_24_000017))
(assert (! (= xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2024_07_27_unit_USD_dims_none 7783) :named xbrl_instance_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2024_07_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2024_07_27_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2024_07_27_unit_USD_dims_none))) 1.5) :named xbrl_calc_27_897844438_PropertyPlantAndEquipmentNet_c_4_upper))
(assert (! (>= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2024_07_27_unit_USD_dims_none (+ xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2024_07_27_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2024_07_27_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_27_897844438_PropertyPlantAndEquipmentNet_c_4_lower))

(check-sat)
(get-unsat-core)
(get-model)