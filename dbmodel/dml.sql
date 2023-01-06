--
-- Default values
--

INSERT INTO asset.config_diameter_def VALUES (12.00, 60.00, 250.00, 10);
INSERT INTO asset.config_diameter_def VALUES (19.00, 65.00, 275.00, 10);
INSERT INTO asset.config_diameter_def VALUES (25.00, 70.00, 300.00, 10);
INSERT INTO asset.config_diameter_def VALUES (32.00, 80.00, 325.00, 10);
INSERT INTO asset.config_diameter_def VALUES (40.00, 90.00, 375.00, 10);
INSERT INTO asset.config_diameter_def VALUES (50.00, 100.00, 400.00, 10);
INSERT INTO asset.config_diameter_def VALUES (63.00, 110.00, 425.00, 10);
INSERT INTO asset.config_diameter_def VALUES (75.00, 120.00, 500.00, 10);
INSERT INTO asset.config_diameter_def VALUES (100.00, 150.00, 550.00, 10);
INSERT INTO asset.config_diameter_def VALUES (125.00, 175.00, 600.00, 10);
INSERT INTO asset.config_diameter_def VALUES (150.00, 200.00, 650.00, 10);
INSERT INTO asset.config_diameter_def VALUES (200.00, 220.00, 750.00, 10);
INSERT INTO asset.config_diameter_def VALUES (250.00, 240.00, 800.00, 10);
INSERT INTO asset.config_diameter_def VALUES (300.00, 260.00, 850.00, 10);
INSERT INTO asset.config_diameter_def VALUES (350.00, 280.00, 900.00, 10);
INSERT INTO asset.config_diameter_def VALUES (400.00, 300.00, 950.00, 10);
INSERT INTO asset.config_diameter_def VALUES (450.00, 320.00, 1000.00, 10);
INSERT INTO asset.config_diameter_def VALUES (500.00, 350.00, 1050.00, 10);
INSERT INTO asset.config_diameter_def VALUES (550.00, 400.00, 1100.00, 10);
INSERT INTO asset.config_diameter_def VALUES (600.00, 450.00, 1150.00, 10);
INSERT INTO asset.config_diameter_def VALUES (700.00, 500.00, 1200.00, 10);
INSERT INTO asset.config_diameter_def VALUES (800.00, 550.00, 1250.00, 10);
INSERT INTO asset.config_diameter_def VALUES (900.00, 600.00, 1300.00, 10);
INSERT INTO asset.config_diameter_def VALUES (1100.00, 650.00, 1350.00, 10);
INSERT INTO asset.config_diameter_def VALUES (1110.00, 700.00, 1400.00, 10);

INSERT INTO asset.config_material_def SELECT id, 0.16, 58, 50, 42, 1964, 10 FROM asset.cat_mat_arc;

INSERT INTO asset.config_engine_def VALUES ('strategic', '0.2', 'S-H', NULL, 'Peso en la matriz final por factores estrategicos', true, 'lyt_weights', 3, 'Weight strategic', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('expected_year', '0.7', 'S-H', NULL, 'Peso en la matriz final por año de renovación', true, 'lyt_weights', 1, 'Weight expected year', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('compliance', '0.1', 'S-H', NULL, 'Peso en la matriz final por cumplimiento normativo', true, 'lyt_weights', 2, 'Weight compliance', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('bratemain0', '0.05', 'S-H', NULL, 'Tasa de crecimiento de fugas tuberias a falta de datos Break rate 0', true, 'lyt_sh_parameters', 1, 'Break rate on mains', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO asset.config_engine_def VALUES ('drate', '0.05', 'S-H', NULL, 'Tasa de actualización real de precios (discount rate). Tiene en cuenta el incremento de precios descontando la inflación', true, 'lyt_sh_parameters', 2, 'Discount rate', 'float', 'text', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

--
-- config_form_tableview
--

INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_diameter_def', 'dnom', 0, true, NULL, 'Diámetro', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_diameter_def', 'cost_constr', 1, true, NULL, 'Coste reconstrucción', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_diameter_def', 'cost_repmain', 2, true, NULL, 'Coste reparación tubería', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_diameter_def', 'cost_repserv', 3, false, NULL, 'Coste reparación acometida', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_diameter_def', 'compliance', 4, true, NULL, 'Normativo', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_diameter_def', 'result_id', 5, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_material_def', 'material', 0, true, NULL, 'Material', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_material_def', 'pleak', 1, true, NULL, 'Prob. de fallo', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_material_def', 'age_max', 2, true, NULL, 'Longevidad máx.', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_material_def', 'age_med', 3, true, NULL, 'Longevidad med.', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_material_def', 'age_min', 4, true, NULL, 'Longevidad mín.', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_material_def', 'builtdate_vdef', 5, true, NULL, 'Año instalación', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_material_def', 'compliance', 6, true, NULL, 'Normativo', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_material_def', 'result_id', 7, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'parameter', 0, true, NULL, 'Parametro', NULL);
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'value', 1, true, NULL, 'Valor', NULL);
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'method', 2, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'round', 3, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'descript', 4, true, NULL, 'Descripción', '{"stretch": true}');
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
INSERT INTO asset.config_form_tableview VALUES ('priority_config', 'utils', 'config_engine_def', 'result_id', 19, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'result_selection', 'id', 0, false, NULL, NULL, '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'result_selection', 'result_id', 1, true, NULL, 'Resultado', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'result_selection', 'selection_id', 2, true, NULL, 'Selección', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'result_selection', 'descript', 3, true, NULL, 'Descripción', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'result_selection', 'arc_id', 4, true, NULL, 'Arco', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'result_selection', 'cur_user', 5, true, NULL, 'Usuario', '{"stretch": true}');
INSERT INTO asset.config_form_tableview VALUES ('priority_manager', 'utils', 'result_selection', 'tstamp', 6, true, NULL, 'Fecha', '{"stretch": true}');
