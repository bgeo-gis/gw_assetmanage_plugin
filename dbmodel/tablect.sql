set search_path = asset;
ALTER TABLE config_diameter
  ADD CONSTRAINT config_diameter_result_id_fkey FOREIGN KEY (result_id)
      REFERENCES cat_result (result_id) MATCH SIMPLE
      ON UPDATE CASCADE ON DELETE CASCADE;


ALTER TABLE config_engine
  ADD CONSTRAINT config_engine_result_id_fkey FOREIGN KEY (result_id)
      REFERENCES cat_result (result_id) MATCH SIMPLE
      ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE config_material
  ADD CONSTRAINT config_material_result_id_fkey FOREIGN KEY (result_id)
      REFERENCES cat_result (result_id) MATCH SIMPLE
      ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE selector_result_compare
  ADD CONSTRAINT selector_result_compare_result_id_fkey FOREIGN KEY (result_id)
      REFERENCES cat_result (result_id) MATCH SIMPLE
      ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE selector_result_main
  ADD CONSTRAINT selector_result_main_result_id_fkey FOREIGN KEY (result_id)
      REFERENCES cat_result (result_id) MATCH SIMPLE
      ON UPDATE CASCADE ON DELETE CASCADE;



ALTER TABLE leaks
  ADD CONSTRAINT leaks_matcat_id_fkey FOREIGN KEY (material)
      REFERENCES cat_mat_arc (id) MATCH SIMPLE
      ON UPDATE CASCADE ON DELETE CASCADE;


ALTER TABLE arc_asset
  ADD CONSTRAINT arc_asset_matcat_id_fkey FOREIGN KEY (matcat_id)
      REFERENCES cat_mat_arc (id) MATCH SIMPLE
      ON UPDATE CASCADE ON DELETE CASCADE;
      
     