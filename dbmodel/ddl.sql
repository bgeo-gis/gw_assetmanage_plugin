
SET search_path = SCHEMA_NAME, public;

CREATE TABLE arc_input
(arc_id integer,
result_id integer,
dnom numeric(12,3),
material character varying(50),
length numeric(12,3),
age smallint ,
longevity numeric(12,3),
rleak numeric(12,3),
ndvi numeric(12,3),
nconn integer,
lconn numeric(12,3),
depth numeric(12,3),
traffic character varying(30),
pressure numeric(12,3),
terrain character varying(50),
pavement character varying(50),
wtable numeric(12,3),
npresszone integer,
nhydro integer,
flow numeric(12,3),
cserv numeric(12,3),
water numeric(12,3),
nrw numeric(12,3),
plan boolean,
social boolean,
other boolean,
mandatory boolean,
compliance boolean,
 CONSTRAINT arc_input_pkey PRIMARY KEY (arc_id, result_id));



CREATE TABLE arc_engine_wm 
(arc_id integer,
result_id integer,
rleak integer,
mleak integer,
ndvi integer,
nconn integer,
lconn integer,
longevity integer,
depth integer,
traffic integer,
pressure integer,
npresszone integer,
terrain integer,
pavement integer,
wtable integer,
nhydro integer,
flow integer,
cserv integer,
water integer,
nrw integer,
strategic integer,
compliance integer,
val_first integer,
val integer,
 CONSTRAINT arc_engine_wm_pkey PRIMARY KEY (arc_id, result_id));


CREATE TABLE arc_engine_sh 
(arc_id integer,
result_id integer,
cost_repmain numeric(12,2),
cost_repserv numeric(12,2),
cost_water numeric(12,2),
cost_nhydr numeric(12,2),
cost_cserv numeric(12,2),
cost_leak numeric(12,2),
cost_constr numeric(12,2),
bratemain numeric(12,3),
brateserv numeric(12,3),
year integer,
year_order integer,
strategic integer,
compliance integer,
val integer,
 CONSTRAINT arc_engine_sh_pkey PRIMARY KEY (arc_id, result_id));



CREATE TABLE arc_output 
(arc_id integer,
result_id integer,
val integer,
mandatory boolean,
orderby integer,
target_year integer,
budget numeric (12,2),
total numeric (12,2),
 CONSTRAINT arc_output_pkey PRIMARY KEY (arc_id, result_id));


CREATE TABLE config_diameter 
(dnom numeric(12,2),
cost_constr	numeric (12,2),
cost_repmain numeric (12,2),
cost_repserv numeric (12,2),
compliance	boolean,
 CONSTRAINT config_diameter_pkey PRIMARY KEY (dnom));


CREATE TABLE config_material 
(material character varying(50),
pleak numeric (12,2),
age_max	smallint,
age_med	smallint,
age_min	smallint,
builtdate_vdef	smallint,
compliance	boolean,
 CONSTRAINT config_material_pkey PRIMARY KEY (material));


CREATE TABLE cat_result
(result_id integer,
descript text,
expl_id integer,
budget numeric(12,2),
current_ivi numeric(12,2),
target_year smallint,
target_ivi numeric(12,2), 
tstamp timestamp,
cur_user text,
status smallint,
 CONSTRAINT cat_result_pkey PRIMARY KEY (result_id));



CREATE TABLE config_engine 
(parameter character varying(50) NOT NULL,
value text,
method	character varying(30),
round smallint,
descript text,
active boolean,
/*layoutname	character varying(50),
layoutorder	integer,
label character varying(200),
datatype character varying(50),
widgettype character varying(50),
dv_querytext text,	
dv_filterbyfield text,
isenabled boolean,
project_type character varying,
dv_isparent boolean,
isautoupdate boolean,
ismandatory boolean,
iseditable boolean,
dv_orderby_id boolean,
dv_isnullvalue boolean,
stylesheet json,
widgetcontrols json,
placeholder text,
standardvalue text,*/
 CONSTRAINT config_engine_pkey PRIMARY KEY (parameter));



CREATE TABLE log_config 
(result_id integer,
cost_water numeric(12,2),
cost_nhydr numeric(12,2),
cost_cserv numeric(12,2),
cost_repserv numeric(12,2),
rleak numeric(12,3),
mleak integer,
ndvi numeric(12,3),
nconn integer,
lconn numeric(12,3),
longevity numeric(12,3),
depth numeric(12,3),
npresszone integer,
traffic character varying(30),
pressure numeric(12,3),
terrain character varying(50),
pavement character varying(50),
wtable numeric(12,3),
nhydro integer,
flow numeric(12,3),
cserv boolean,
bratemain numeric(12,3),
brateserv numeric(12,3),
drate numeric(12,3),
risk numeric(12,3),
nrw numeric(12,3),
compliance integer,
strategic integer,
 CONSTRAINT log_config_pkey PRIMARY KEY (result_id));


CREATE TABLE leaks
(id serial, 
ext_code text, 
address text, 
province character varying(100),
county character varying(100),
district character varying(100),
system character varying(100),
zone character varying(100),
type text,
material character varying(100), 
startdate date, 
enddate date, 
days integer, 
the_geom geometry(Point,5367),
 CONSTRAINT leaks_pkey PRIMARY KEY (id));


CREATE TABLE arc_asset
(arc_id integer,
code text,
sector_id integer,
macrosector_id integer,
pressurezone_id character varying(30),
expl_id integer,
builtdate  date,
dnom integer,
matcat_id character varying(30),
pavcat_id character varying(30),
function_type character varying(50),
the_geom geometry(Linestring,5367),
 CONSTRAINT arc_asset_pkey PRIMARY KEY (arc_id));


CREATE TABLE selector_result
(
  result_id integer NOT NULL,
  cur_user text NOT NULL DEFAULT "current_user"(),
  CONSTRAINT selector_result_pkey PRIMARY KEY (result_id, cur_user),
  CONSTRAINT cat_result_result_id_fkey FOREIGN KEY (result_id)
      REFERENCES cat_result (result_id) MATCH SIMPLE
      ON UPDATE CASCADE ON DELETE CASCADE
);



CREATE TABLE macrosector (
  macrosector_id serial4 NOT NULL,
  name text,
  the_geom public.geometry(multipolygon, 5367),
  CONSTRAINT macrosector_pkey PRIMARY KEY (macrosector_id)
);

CREATE TABLE sector (
  sector_id serial4 NOT NULL,
  name text,
  macrosector_id int4,
  the_geom public.geometry(multipolygon, 5367),
  CONSTRAINT sector_pkey PRIMARY KEY (sector_id)
);
  


CREATE TABLE presszone (
  presszone_id serial4 NOT NULL,
  name text,
  the_geom public.geometry(multipolygon, 5367),
  CONSTRAINT presszone_pkey PRIMARY KEY (presszone_id)
);

CREATE TABLE exploitation (
  expl_id serial4 NOT NULL,
  "name" text,
  the_geom public.geometry(multipolygon, 5367),
  CONSTRAINT exploitation_pkey PRIMARY KEY (expl_id)
);

CREATE OR REPLACE VIEW v_asset_arc_input
 AS
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
   FROM arc_asset a
     LEFT JOIN arc_input i USING (arc_id);

CREATE OR REPLACE VIEW v_asset_arc_output
 AS
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
    a.the_geom
   FROM arc_asset a,
     LEFT JOIN arc_input i USING (arc_id)
     JOIN arc_output o USING (arc_id)
     JOIN selector_result_main s ON s.result_id = o.result_id
  WHERE s.cur_user = CURRENT_USER::text;
