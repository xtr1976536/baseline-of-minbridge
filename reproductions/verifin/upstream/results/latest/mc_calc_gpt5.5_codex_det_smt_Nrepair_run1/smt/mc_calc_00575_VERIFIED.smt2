(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_property_plant_and_equipment_net_fy2023 Real)
(declare-const accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023 Real)
(declare-const property_plant_and_equipment_gross_fy2023 Real)

(assert (! (= accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023 16045) :named evidence_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023))
(assert (! (= property_plant_and_equipment_gross_fy2023 34985) :named evidence_property_plant_and_equipment_gross_fy2023))

(assert (! (= computed_property_plant_and_equipment_net_fy2023 (+ property_plant_and_equipment_gross_fy2023 (* (- 1) accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023))) :named formula_property_plant_and_equipment_net_fy2023))

(assert (! (<= (- computed_property_plant_and_equipment_net_fy2023 18940) 18.940000000000001) :named claim_upper))
(assert (! (<= (- 18940 computed_property_plant_and_equipment_net_fy2023) 18.940000000000001) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2023_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2023_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2023_12_31_unit_USD_dims_none 18940) :named evidence_xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2023_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= property_plant_and_equipment_gross_fy2023 xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_property_plant_and_equipment_gross_fy2023_edgar_2023_12_31_0000078003_24_000039))
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2023_12_31_unit_USD_dims_none 34985) :named xbrl_instance_property_plant_and_equipment_gross_fy2023))
(assert (! (= accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2023_12_31_unit_USD_dims_none) :named xbrl_bind_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023_edgar_2023_12_31_0000078003_24_000039))
(assert (! (= xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2023_12_31_unit_USD_dims_none 16045) :named xbrl_instance_accumulated_depreciation_depletion_and_amortization_property_plant_and_equipment_fy2023))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2023_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2023_12_31_unit_USD_dims_none))) 1.5) :named xbrl_calc_73_197381787_PropertyPlantAndEquipmentNet_c_8_upper))
(assert (! (>= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2023_12_31_unit_USD_dims_none (+ xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2023_12_31_unit_USD_dims_none (* -1 xbrl_fact_us_gaap_AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment_instant_2023_12_31_unit_USD_dims_none))) (- 1.5)) :named xbrl_calc_73_197381787_PropertyPlantAndEquipmentNet_c_8_lower))

(check-sat)
(get-unsat-core)
(get-model)