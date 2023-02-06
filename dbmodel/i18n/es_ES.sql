INSERT INTO asset.value_result_type VALUES ('GLOBAL', 'GLOBAL');
INSERT INTO asset.value_result_type VALUES ('SELECTION', 'SELECCIÓN');

INSERT INTO asset.value_status VALUES ('CANCELED', 'CANCELADO');
INSERT INTO asset.value_status VALUES ('ON PLANNING', 'EN PLANIFICACIÓN');
INSERT INTO asset.value_status VALUES ('FINISHED', 'FINALIZADO');

UPDATE asset.config_engine_def SET descript = 'Peso en matriz final por factores estratégicos' WHERE parameter = 'strategic' AND method = 'SH';
UPDATE asset.config_engine_def SET descript = 'Peso en matriz final por año de renovación' WHERE parameter = 'expected_year' AND method = 'SH';
UPDATE asset.config_engine_def SET descript = 'Peso en matriz final por cumplimiento normativo' WHERE parameter = 'compliance' AND method = 'SH';
UPDATE asset.config_engine_def SET descript = 'Tasa de crecimiento de fugas en tuberías' WHERE parameter = 'bratemain0' AND method = 'SH';
UPDATE asset.config_engine_def SET descript = 'Tasa de actualización real de precios (discount rate). Tiene en cuenta el aumento de precios descontando la inflación' WHERE parameter = 'drate' AND method = 'SH';

UPDATE asset.config_form_tableview SET alias = 'Diámetro' WHERE tablename = 'config_cost_def' AND columnname = 'dnom';
UPDATE asset.config_form_tableview SET alias = 'Coste reconstrucción' WHERE tablename = 'config_cost_def' AND columnname = 'cost_constr';
UPDATE asset.config_form_tableview SET alias = 'Coste reparación tubería' WHERE tablename = 'config_cost_def' AND columnname = 'cost_repmain';
UPDATE asset.config_form_tableview SET alias = 'Coste reparación acometida' WHERE tablename = 'config_cost_def' AND columnname = 'cost_repserv';
UPDATE asset.config_form_tableview SET alias = 'Normativo' WHERE tablename = 'config_cost_def' AND columnname = 'compliance';
UPDATE asset.config_form_tableview SET alias = 'Material' WHERE tablename = 'config_material_def' AND columnname = 'material';
UPDATE asset.config_form_tableview SET alias = 'Prob. de fallo' WHERE tablename = 'config_material_def' AND columnname = 'pleak';
UPDATE asset.config_form_tableview SET alias = 'Longevidad máx.' WHERE tablename = 'config_material_def' AND columnname = 'age_max';
UPDATE asset.config_form_tableview SET alias = 'Longevidad med.' WHERE tablename = 'config_material_def' AND columnname = 'age_med';
UPDATE asset.config_form_tableview SET alias = 'Longevidad mín.' WHERE tablename = 'config_material_def' AND columnname = 'age_min';
UPDATE asset.config_form_tableview SET alias = 'Año instalación' WHERE tablename = 'config_material_def' AND columnname = 'builtdate_vdef';
UPDATE asset.config_form_tableview SET alias = 'Normativo' WHERE tablename = 'config_material_def' AND columnname = 'compliance';
UPDATE asset.config_form_tableview SET alias = 'Parámetro' WHERE tablename = 'config_engine_def' AND columnname = 'parameter';
UPDATE asset.config_form_tableview SET alias = 'Valor' WHERE tablename = 'config_engine_def' AND columnname = 'value';
UPDATE asset.config_form_tableview SET alias = 'Descripción' WHERE tablename = 'config_engine_def' AND columnname = 'alias';
UPDATE asset.config_form_tableview SET alias = 'Id' WHERE tablename = 'cat_result' AND columnname = 'result_id';
UPDATE asset.config_form_tableview SET alias = 'Resultado' WHERE tablename = 'cat_result' AND columnname = 'result_name';
UPDATE asset.config_form_tableview SET alias = 'Tipo' WHERE tablename = 'cat_result' AND columnname = 'result_type';
UPDATE asset.config_form_tableview SET alias = 'Descripción' WHERE tablename = 'cat_result' AND columnname = 'descript';
UPDATE asset.config_form_tableview SET alias = 'Fecha' WHERE tablename = 'cat_result' AND columnname = 'tstamp';
UPDATE asset.config_form_tableview SET alias = 'Usuario' WHERE tablename = 'cat_result' AND columnname = 'cur_user';
UPDATE asset.config_form_tableview SET alias = 'Status' WHERE tablename = 'cat_result' AND columnname = 'status';
UPDATE asset.config_form_tableview SET alias = 'Selección' WHERE tablename = 'cat_result' AND columnname = 'features';