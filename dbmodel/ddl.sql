
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
layoutname	character varying(50),
layoutorder	integer,
label character varying(200),
datatype character varying(50),
widgettype character varying(50),
dv_querytext text,	
dv_controls	json,
ismandatory	boolean,
iseditable boolean,
stylesheet json, 
widgetcontrols json,
placeholder	text,
standardvalue text,
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
sector_id integer,
macrosector_id integer,
pressurezone_id character varying(30),
builtdate  date,
dnom integer,
matcat_id character varying(30),
pavcat_id character varying(30),
function_type character varying(50),
the_geom geometry(Linestring,5367),
 CONSTRAINT arc_asset_pkey PRIMARY KEY (arc_id));