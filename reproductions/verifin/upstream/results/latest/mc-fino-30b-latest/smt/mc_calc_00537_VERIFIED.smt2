(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_property_plant_and_equipment_net_fy2024 Real)
(declare-const property_plant_and_equipment_gross_fy2024 Real)
(declare-const property_plant_and_equipment_owned_accumulated_depreciation_fy2024 Real)

(assert (! (= property_plant_and_equipment_gross_fy2024 19873) :named evidence_property_plant_and_equipment_gross_fy2024))
(assert (! (= property_plant_and_equipment_owned_accumulated_depreciation_fy2024 9570) :named evidence_property_plant_and_equipment_owned_accumulated_depreciation_fy2024))

(assert (! (= computed_property_plant_and_equipment_net_fy2024 (+ (* (- 1) property_plant_and_equipment_owned_accumulated_depreciation_fy2024) property_plant_and_equipment_gross_fy2024)) :named formula_property_plant_and_equipment_net_fy2024))

(assert (! (<= (- computed_property_plant_and_equipment_net_fy2024 10303) 10.303000000000001) :named claim_upper))
(assert (! (<= (- 10303 computed_property_plant_and_equipment_net_fy2024) 10.303000000000001) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2024_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentOwnedAccumulatedDepreciation_instant_2024_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2024_12_31_unit_USD_dims_none 10303) :named evidence_xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2024_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= property_plant_and_equipment_owned_accumulated_depreciation_fy2024 xbrl_fact_us_gaap_PropertyPlantAndEquipmentOwnedAccumulatedDepreciation_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_property_plant_and_equipment_owned_accumulated_depreciation_fy2024_edgar_2024_12_31_0000021344_25_000011))
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentOwnedAccumulatedDepreciation_instant_2024_12_31_unit_USD_dims_none 9570) :named xbrl_instance_property_plant_and_equipment_owned_accumulated_depreciation_fy2024))
(assert (! (= property_plant_and_equipment_gross_fy2024 xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2024_12_31_unit_USD_dims_none) :named xbrl_bind_property_plant_and_equipment_gross_fy2024_edgar_2024_12_31_0000021344_25_000011))
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2024_12_31_unit_USD_dims_none 19873) :named xbrl_instance_property_plant_and_equipment_gross_fy2024))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2024_12_31_unit_USD_dims_none (+ (* -1 xbrl_fact_us_gaap_PropertyPlantAndEquipmentOwnedAccumulatedDepreciation_instant_2024_12_31_unit_USD_dims_none) xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2024_12_31_unit_USD_dims_none)) 1.5) :named xbrl_calc_21_868343572_PropertyPlantAndEquipmentNet_c_28_upper))
(assert (! (>= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2024_12_31_unit_USD_dims_none (+ (* -1 xbrl_fact_us_gaap_PropertyPlantAndEquipmentOwnedAccumulatedDepreciation_instant_2024_12_31_unit_USD_dims_none) xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2024_12_31_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_21_868343572_PropertyPlantAndEquipmentNet_c_28_lower))

(check-sat)
(get-unsat-core)
(get-model)