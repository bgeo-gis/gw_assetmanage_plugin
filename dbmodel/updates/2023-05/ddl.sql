ALTER TABLE asset.config_catalog_def ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE asset.value_result_type ADD PRIMARY KEY (id);
ALTER TABLE asset.value_status ADD PRIMARY KEY (id);