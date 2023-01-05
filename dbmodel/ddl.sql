CREATE SCHEMA asset;

SET search_path = asset, public;

--
-- TABLES:
--

CREATE TABLE asset.leaks (
    id serial,
    material character varying(100),
    diameter integer,
    "date" date,
    the_geom public.geometry(MultiPoint,SCHEMA_SRID),
    CONSTRAINT leaks_pkey PRIMARY KEY (id)
);

CREATE TABLE asset.arc_input (
    arc_id character varying(60) NOT NULL,
    longevity numeric(12,3),
    rleak numeric(12,3),
    pressure numeric(12,3),
    flow numeric(12,3),
    nrw numeric(12,3),
    strategic boolean,
    mandatory boolean,
    compliance integer,
    CONSTRAINT arc_input_pkey PRIMARY KEY (arc_id)
);

CREATE TABLE asset.cat_result (
    result_id serial,
    result_name text,
    result_type character varying(50),
    descript text,
    expl_id integer,
    budget numeric(12,2),
    _current_ivi numeric(12,2),
    target_year smallint,
    _target_ivi numeric(12,2),
    tstamp timestamp without time zone,
    cur_user text,
    status smallint,
    presszone_id character varying(30),
    material_id character varying(30),
    features character varying[],
    dnom numeric(12,3),
    CONSTRAINT cat_result_pkey PRIMARY KEY (result_id),
    CONSTRAINT cat_result_result_type_check CHECK (((result_type)::text = ANY (ARRAY[('GLOBAL'::character varying)::text, ('SELECTION'::character varying)::text])))
);

CREATE TABLE asset.config_diameter_def (
    dnom numeric(12,2) NOT NULL,
    cost_constr numeric(12,2),
    cost_repmain numeric(12,2),
    compliance integer,
    CONSTRAINT config_diameter_def_pkey PRIMARY KEY (dnom)
);

CREATE TABLE asset.config_diameter (
    dnom numeric(12,2) NOT NULL,
    cost_constr numeric(12,2),
    cost_repmain numeric(12,2),
    compliance integer,
    result_id integer NOT NULL,
    CONSTRAINT config_diameter_pkey PRIMARY KEY (dnom, result_id)
);

CREATE TABLE asset.config_material_def (
    material character varying(50) NOT NULL,
    pleak numeric(12,2),
    age_max smallint,
    age_med smallint,
    age_min smallint,
    builtdate_vdef smallint,
    compliance integer,
    CONSTRAINT config_material_def_pkey PRIMARY KEY (material)
);

CREATE TABLE asset.config_material (
    material character varying(50) NOT NULL,
    pleak numeric(12,2),
    age_max smallint,
    age_med smallint,
    age_min smallint,
    builtdate_vdef smallint,
    compliance integer,
    result_id integer NOT NULL,
    CONSTRAINT config_material_pkey PRIMARY KEY (material, result_id)
);

CREATE TABLE asset.config_engine_def (
    parameter character varying(50) NOT NULL,
    value text,
    method character varying(30),
    round smallint,
    descript text,
    active boolean,
    layoutname character varying(50),
    layoutorder integer,
    label character varying(200),
    datatype character varying(50),
    widgettype character varying(50),
    dv_querytext text,
    dv_controls json,
    ismandatory boolean,
    iseditable boolean,
    stylesheet json,
    widgetcontrols json,
    placeholder text,
    standardvalue text,
    CONSTRAINT config_engine_def_pkey PRIMARY KEY (parameter, method)
);

CREATE TABLE asset.config_engine (
    parameter character varying(50) NOT NULL,
    value text,
    method character varying(30),
    round smallint,
    descript text,
    active boolean,
    layoutname character varying(50),
    layoutorder integer,
    label character varying(200),
    datatype character varying(50),
    widgettype character varying(50),
    dv_querytext text,
    dv_controls json,
    ismandatory boolean,
    iseditable boolean,
    stylesheet json,
    widgetcontrols json,
    placeholder text,
    standardvalue text,
    result_id integer NOT NULL,
    CONSTRAINT config_engine_pkey PRIMARY KEY (parameter, result_id)
);

CREATE TABLE asset.arc_engine_sh (
    arc_id character varying(16) NOT NULL,
    result_id integer NOT NULL,
    cost_repmain numeric(12,2),
    cost_constr numeric(12,2),
    bratemain numeric(12,3),
    brateserv numeric(12,3),
    year integer,
    year_order double precision,
    strategic integer,
    compliance integer,
    val double precision,
    CONSTRAINT arc_engine_sh_pkey PRIMARY KEY (arc_id, result_id)
);

CREATE TABLE asset.arc_engine_wm (
    arc_id character varying(16) NOT NULL,
    result_id integer NOT NULL,
    rleak integer,
    longevity integer,
    pressure integer,
    flow integer,
    nrw integer,
    strategic integer,
    compliance integer,
    val_first double precision,
    val double precision,
    CONSTRAINT arc_engine_wm_pkey PRIMARY KEY (arc_id, result_id)
);

CREATE TABLE asset.arc_output (
    arc_id character varying(16) NOT NULL,
    result_id integer NOT NULL,
    val double precision,
    mandatory boolean,
    orderby integer,
    expected_year integer,
    budget numeric(12,2),
    total numeric(12,2),
    length numeric(12,3),
    cum_length numeric(12,3),
    CONSTRAINT arc_output_pkey PRIMARY KEY (arc_id, result_id)
);

CREATE TABLE asset.selector_result_main (
    -- TODO: check FK
    result_id integer NOT NULL,
    cur_user text DEFAULT "current_user"() NOT NULL,
    CONSTRAINT selector_result_main_pkey PRIMARY KEY (cur_user, result_id)
);

CREATE TABLE asset.selector_result_compare (
    -- TODO: check FK
    result_id integer NOT NULL,
    cur_user text DEFAULT "current_user"() NOT NULL,
    CONSTRAINT selector_result_compare_pkey PRIMARY KEY (cur_user, result_id)
);

CREATE TABLE asset.config_form_tableview (
    location_type character varying(50) NOT NULL,
    project_type character varying(50) NOT NULL,
    tablename character varying(50) NOT NULL,
    columnname character varying(50) NOT NULL,
    columnindex smallint,
    visible boolean,
    width integer,
    alias character varying(50),
    style json,
    CONSTRAINT config_form_tableview_pkey PRIMARY KEY (tablename, columnname)
);

--
-- VIEWS:
--

CREATE VIEW asset.exploitation AS
 SELECT exploitation.expl_id,
    exploitation.name,
    exploitation.the_geom
   FROM PARENT_SCHEMA.exploitation;

CREATE VIEW asset.macrosector AS
 SELECT macrosector.macrosector_id,
    macrosector.name,
    macrosector.the_geom
   FROM PARENT_SCHEMA.macrosector;

CREATE VIEW asset.sector AS
 SELECT sector.sector_id,
    sector.name,
    sector.macrosector_id,
    sector.the_geom
   FROM PARENT_SCHEMA.sector;

CREATE VIEW asset.presszone AS
 SELECT presszone.presszone_id,
    presszone.name,
    presszone.the_geom
   FROM PARENT_SCHEMA.presszone;

CREATE VIEW asset.cat_mat_arc AS
 SELECT cat_mat_arc.id,
    cat_mat_arc.descript
   FROM PARENT_SCHEMA.cat_mat_arc
  WHERE (cat_mat_arc.active = true);

CREATE VIEW asset.arc_asset AS
 SELECT v_edit_arc.arc_id,
    v_edit_arc.sector_id,
    v_edit_arc.macrosector_id,
    v_edit_arc.presszone_id,
    v_edit_arc.builtdate,
    v_edit_arc.cat_dnom AS dnom,
    v_edit_arc.cat_matcat_id AS matcat_id,
    v_edit_arc.pavcat_id,
    v_edit_arc.function_type,
    v_edit_arc.the_geom,
    v_edit_arc.code,
    v_edit_arc.expl_id
   FROM PARENT_SCHEMA.v_edit_arc;

CREATE VIEW asset.v_asset_arc_input AS
 SELECT a.arc_id,
    a.sector_id,
    a.macrosector_id,
    a.presszone_id,
    a.expl_id,
    a.builtdate,
    a.dnom,
    a.matcat_id,
    a.pavcat_id,
    a.function_type,
    i.rleak,
    a.the_geom
   FROM (asset.arc_asset a
     LEFT JOIN asset.arc_input i USING (arc_id));

CREATE VIEW asset.v_asset_arc_output AS
 SELECT a.arc_id,
    o.result_id,
    a.sector_id,
    a.macrosector_id,
    a.presszone_id,
    a.expl_id,
    a.builtdate,
    a.dnom,
    a.matcat_id,
    a.pavcat_id,
    a.function_type,
    i.rleak,
    o.val,
    o.orderby,
    o.expected_year,
    o.budget,
    o.total,
    a.the_geom,
    o.length,
    o.cum_length
   FROM (((asset.arc_asset a
     LEFT JOIN asset.arc_input i USING (arc_id))
     JOIN asset.arc_output o USING (arc_id))
     JOIN asset.selector_result_main s ON ((s.result_id = o.result_id)))
  WHERE (s.cur_user = (CURRENT_USER)::text);

CREATE VIEW asset.v_asset_arc_output_compare AS
 SELECT a.arc_id,
    o.result_id,
    a.sector_id,
    a.macrosector_id,
    a.presszone_id,
    a.expl_id,
    a.builtdate,
    a.dnom,
    a.matcat_id,
    a.pavcat_id,
    a.function_type,
    i.rleak,
    o.val,
    o.orderby,
    o.expected_year,
    o.budget,
    o.total,
    a.the_geom,
    o.length,
    o.cum_length
   FROM (((asset.arc_asset a
     LEFT JOIN asset.arc_input i USING (arc_id))
     JOIN asset.arc_output o USING (arc_id))
     JOIN asset.selector_result_compare s ON ((s.result_id = o.result_id)))
  WHERE (s.cur_user = (CURRENT_USER)::text);
