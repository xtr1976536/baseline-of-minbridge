(set-logic QF_NRA)
(set-option :produce-unsat-cores true)
(set-option :produce-models true)

(declare-const computed_property_plant_and_equipment_net_fy2025 Real)
(declare-const property_plant_and_equipment_gross_fy2025 Real)
(declare-const property_plant_and_equipment_owned_accumulated_depreciation_fy2025 Real)

(assert (! (= property_plant_and_equipment_gross_fy2025 18732) :named evidence_property_plant_and_equipment_gross_fy2025))
(assert (! (= property_plant_and_equipment_owned_accumulated_depreciation_fy2025 9119) :named evidence_property_plant_and_equipment_owned_accumulated_depreciation_fy2025))

(assert (! (= computed_property_plant_and_equipment_net_fy2025 (+ (* (- 1) property_plant_and_equipment_owned_accumulated_depreciation_fy2025) property_plant_and_equipment_gross_fy2025)) :named formula_property_plant_and_equipment_net_fy2025))

(assert (! (<= (- computed_property_plant_and_equipment_net_fy2025 9613) 9.6129999999999995) :named claim_upper))
(assert (! (<= (- 9613 computed_property_plant_and_equipment_net_fy2025) 9.6129999999999995) :named claim_lower))

; EDGAR-companyfacts calculation-linkbase constraints parsed from the filing.
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2025_12_31_unit_USD_dims_none Real)
(declare-const xbrl_fact_us_gaap_PropertyPlantAndEquipmentOwnedAccumulatedDepreciation_instant_2025_12_31_unit_USD_dims_none Real)

; Redundant XBRL instance facts used only by calculation-linkbase constraints.
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2025_12_31_unit_USD_dims_none 9613) :named evidence_xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2025_12_31_unit_USD_dims_none))

; IR-to-EDGAR-companyfacts bindings and independent instance-value witnesses.
(assert (! (= property_plant_and_equipment_owned_accumulated_depreciation_fy2025 xbrl_fact_us_gaap_PropertyPlantAndEquipmentOwnedAccumulatedDepreciation_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_property_plant_and_equipment_owned_accumulated_depreciation_fy2025_edgar_2025_12_31_0001628280_26_010047))
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentOwnedAccumulatedDepreciation_instant_2025_12_31_unit_USD_dims_none 9119) :named xbrl_instance_property_plant_and_equipment_owned_accumulated_depreciation_fy2025))
(assert (! (= property_plant_and_equipment_gross_fy2025 xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2025_12_31_unit_USD_dims_none) :named xbrl_bind_property_plant_and_equipment_gross_fy2025_edgar_2025_12_31_0001628280_26_010047))
(assert (! (= xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2025_12_31_unit_USD_dims_none 18732) :named xbrl_instance_property_plant_and_equipment_gross_fy2025))

; R constraints from filing calculationArc summation-item relationships.
(assert (! (<= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2025_12_31_unit_USD_dims_none (+ (* -1 xbrl_fact_us_gaap_PropertyPlantAndEquipmentOwnedAccumulatedDepreciation_instant_2025_12_31_unit_USD_dims_none) xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2025_12_31_unit_USD_dims_none)) 1.5) :named xbrl_calc_21_868343572_PropertyPlantAndEquipmentNet_c_29_upper))
(assert (! (>= (- xbrl_fact_us_gaap_PropertyPlantAndEquipmentNet_instant_2025_12_31_unit_USD_dims_none (+ (* -1 xbrl_fact_us_gaap_PropertyPlantAndEquipmentOwnedAccumulatedDepreciation_instant_2025_12_31_unit_USD_dims_none) xbrl_fact_us_gaap_PropertyPlantAndEquipmentGross_instant_2025_12_31_unit_USD_dims_none)) (- 1.5)) :named xbrl_calc_21_868343572_PropertyPlantAndEquipmentNet_c_29_lower))

(check-sat)
(get-unsat-core)
(get-model)