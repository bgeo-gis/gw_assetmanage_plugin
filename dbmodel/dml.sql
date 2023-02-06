--
-- Default values
--

INSERT INTO asset.config_cost_def VALUES (12.00, 60.00, 250.00, 10);
INSERT INTO asset.config_cost_def VALUES (19.00, 65.00, 275.00, 10);
INSERT INTO asset.config_cost_def VALUES (25.00, 70.00, 300.00, 10);
INSERT INTO asset.config_cost_def VALUES (32.00, 80.00, 325.00, 10);
INSERT INTO asset.config_cost_def VALUES (40.00, 90.00, 375.00, 10);
INSERT INTO asset.config_cost_def VALUES (50.00, 100.00, 400.00, 10);
INSERT INTO asset.config_cost_def VALUES (63.00, 110.00, 425.00, 10);
INSERT INTO asset.config_cost_def VALUES (75.00, 120.00, 500.00, 10);
INSERT INTO asset.config_cost_def VALUES (100.00, 150.00, 550.00, 10);
INSERT INTO asset.config_cost_def VALUES (125.00, 175.00, 600.00, 10);
INSERT INTO asset.config_cost_def VALUES (150.00, 200.00, 650.00, 10);
INSERT INTO asset.config_cost_def VALUES (200.00, 220.00, 750.00, 10);
INSERT INTO asset.config_cost_def VALUES (250.00, 240.00, 800.00, 10);
INSERT INTO asset.config_cost_def VALUES (300.00, 260.00, 850.00, 10);
INSERT INTO asset.config_cost_def VALUES (350.00, 280.00, 900.00, 10);
INSERT INTO asset.config_cost_def VALUES (400.00, 300.00, 950.00, 10);
INSERT INTO asset.config_cost_def VALUES (450.00, 320.00, 1000.00, 10);
INSERT INTO asset.config_cost_def VALUES (500.00, 350.00, 1050.00, 10);
INSERT INTO asset.config_cost_def VALUES (550.00, 400.00, 1100.00, 10);
INSERT INTO asset.config_cost_def VALUES (600.00, 450.00, 1150.00, 10);
INSERT INTO asset.config_cost_def VALUES (700.00, 500.00, 1200.00, 10);
INSERT INTO asset.config_cost_def VALUES (800.00, 550.00, 1250.00, 10);
INSERT INTO asset.config_cost_def VALUES (900.00, 600.00, 1300.00, 10);
INSERT INTO asset.config_cost_def VALUES (1100.00, 650.00, 1350.00, 10);
INSERT INTO asset.config_cost_def VALUES (1110.00, 700.00, 1400.00, 10);

INSERT INTO asset.config_material_def SELECT id, 0.16, 58, 50, 42, 1964, 10 FROM asset.cat_mat_arc;

-- TODO: translate labels
INSERT INTO asset.config_engine_def VALUES ('bratemain0', '0.05', 'SH', NULL, NULL, true, 'lyt_engine_1', 1, 'Break rate on mains', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('drate', '0.05', 'SH', NULL, NULL, true, 'lyt_engine_1', 2, 'Discount rate', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('expected_year', '0.7', 'SH', NULL, NULL, true, 'lyt_engine_2', 1, 'Weight expected year', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('compliance', '0.1', 'SH', NULL, NULL, true, 'lyt_engine_2', 2, 'Weight compliance', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('strategic', '0.2', 'SH', NULL, NULL, true, 'lyt_engine_2', 3, 'Weight strategic', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('rleak_1', '0.2', 'WM', NULL, NULL, true, 'lyt_engine_1', 1, 'Roturas reales', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('rleak_2', '0.0', 'WM', NULL, NULL, true, 'lyt_engine_2', 1, 'Roturas reales', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('mleak_1', '0.1', 'WM', NULL, NULL, true, 'lyt_engine_1', 2, 'Roturas por material', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('mleak_2', '0.0', 'WM', NULL, NULL, true, 'lyt_engine_2', 2, 'Roturas por material', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('longevity_1', '0.7', 'WM', NULL, NULL, true, 'lyt_engine_1', 3, 'Longevidad', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('longevity_2', '0.0', 'WM', NULL, NULL, true, 'lyt_engine_2', 3, 'Longevidad', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('flow_1', '0.0', 'WM', NULL, NULL, true, 'lyt_engine_1', 4, 'Caudal circulante', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('flow_2', '0.5', 'WM', NULL, NULL, true, 'lyt_engine_2', 4, 'Caudal circulante', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('nrw_1', '0.0', 'WM', NULL, NULL, true, 'lyt_engine_1', 5, 'ANC', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('nrw_2', '0.2', 'WM', NULL, NULL, true, 'lyt_engine_2', 5, 'ANC', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('strategic_1', '0.0', 'WM', NULL, NULL, true, 'lyt_engine_1', 6, 'Strategic', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('strategic_2', '0.0', 'WM', NULL, NULL, true, 'lyt_engine_2', 6, 'Strategic', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('compliance_1', '0.0', 'WM', NULL, NULL, true, 'lyt_engine_1', 7, 'Normativo', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('compliance_2', '0.3', 'WM', NULL, NULL, true, 'lyt_engine_2', 7, 'Normativo', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

--
-- config_form_tableview
--

INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_cost_def', 'dnom', 0, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_cost_def', 'cost_constr', 1, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_cost_def', 'cost_repmain', 2, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_cost_def', 'compliance', 3, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_material_def', 'material', 0, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_material_def', 'pleak', 1, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_material_def', 'age_max', 2, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_material_def', 'age_med', 3, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_material_def', 'age_min', 4, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_material_def', 'builtdate_vdef', 5, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_material_def', 'compliance', 6, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'parameter', 0, true, NULL, NULL, NULL);
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'value', 1, true, NULL, NULL, NULL);
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'method', 2, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'round', 3, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'descript', 4, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'active', 5, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'layoutname', 6, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'layoutorder', 7, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'label', 8, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'datatype', 9, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'widgettype', 10, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'dv_querytext', 11, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'dv_controls', 12, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'ismandatory', 13, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'iseditable', 14, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'stylesheet', 15, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'widgetcontrols', 16, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'planceholder', 17, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'standardvalue', 18, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', 'result_id', 0, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', 'result_name', 1, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', 'result_type', 2, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', 'descript', 3, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', 'expl_id', 4, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', 'budget', 5, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', '_current_ivi', 6, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', 'target_year', 7, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', '_target_ivi', 8, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', 'tstamp', 9, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', 'cur_user', 10, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', 'status', 11, true, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', 'presszone_id', 12, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', 'material_id', 13, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', 'features', 14, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'cat_result', 'dnom', 15, false, NULL, NULL, '{"stretch": true}');
