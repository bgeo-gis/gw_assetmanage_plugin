ALTER TABLE asset.config_diameter
    ADD CONSTRAINT config_diameter_result_id_fkey FOREIGN KEY (result_id)
    REFERENCES asset.cat_result(result_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE asset.config_engine
    ADD CONSTRAINT config_engine_result_id_fkey FOREIGN KEY (result_id)
    REFERENCES asset.cat_result(result_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE asset.config_material
    ADD CONSTRAINT config_material_result_id_fkey FOREIGN KEY (result_id)
    REFERENCES asset.cat_result(result_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE asset.selector_result_compare
    ADD CONSTRAINT selector_result_compare_result_id_fkey FOREIGN KEY (result_id)
    REFERENCES asset.cat_result(result_id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE asset.selector_result_main
    ADD CONSTRAINT selector_result_main_result_id_fkey FOREIGN KEY (result_id)
    REFERENCES asset.cat_result(result_id) ON UPDATE CASCADE ON DELETE CASCADE;
