/*
Copyright © 2023 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
*/

ALTER TABLE asset.config_catalog_def ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE asset.value_result_type ADD PRIMARY KEY (id);
ALTER TABLE asset.value_status ADD PRIMARY KEY (id);