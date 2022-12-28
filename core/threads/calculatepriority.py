import configparser
from math import log, log1p, exp
from pathlib import Path

from qgis.core import QgsTask
from qgis.PyQt.QtCore import pyqtSignal

from .task import GwTask
from ... import global_vars
from ...settings import tools_db


def get_min_greater_than(iterable, value):
    result = None
    for item in iterable:
        if item <= value:
            continue
        if result is None or item < result:
            result = item
    return result


def optimal_replacement_time(
    present_year,
    number_of_breaks,
    break_growth_rate,
    repairing_cost,
    replacement_cost,
    discount_rate,
):
    BREAKS_YEAR_0 = 0.05
    optimal_replacement_cycle = (1 / break_growth_rate) * log(
        log1p(discount_rate) * replacement_cost / BREAKS_YEAR_0 / repairing_cost
    )
    cycle_costs = 0
    for t in range(1, round(optimal_replacement_cycle) + 1):
        # print(cycle_costs)
        cycle_costs += (
            repairing_cost
            * BREAKS_YEAR_0
            * exp(break_growth_rate * t)
            / (1 + discount_rate) ** t
        )

    b_orc = 1 / ((1 + discount_rate) ** optimal_replacement_cycle - 1)

    return present_year + (1 / break_growth_rate) * log(
        log1p(discount_rate)
        # * replacement_cost
        * ((replacement_cost + cycle_costs) * b_orc + replacement_cost)
        / number_of_breaks
        / repairing_cost
    )


class GwCalculatePriority(GwTask):
    report = pyqtSignal(dict)
    step = pyqtSignal(str)

    def __init__(
        self,
        description,
        result_type,
        result_name,
        result_description,
        features,
        exploitation,
        presszone,
        diameter,
        material,
        budget,
        target_year,
        config_diameter,
        config_material,
        config_engine,
    ):
        super().__init__(description, QgsTask.CanCancel)
        self.result_type = result_type
        self.result_name = result_name
        self.result_description = result_description
        self.features = features
        self.exploitation = exploitation
        self.presszone = presszone
        self.diameter = diameter
        self.material = material
        self.result_budget = budget
        self.result_target_year = target_year
        self.config_diameter = config_diameter
        self.config_material = config_material
        self.config_engine = config_engine

        config_path = Path(global_vars.plugin_dir) / "config" / "config.config"
        config = configparser.ConfigParser()
        config.read(config_path)
        self.method = config.get("general", "engine_method")

    def run(self):
        try:
            if self.method == "SH":
                return self._run_sh()
            elif self.method == "WM":
                return self._run_wm()
            else:
                raise ValueError("The method is not defined in the configuration file.")

        except Exception as e:
            self._emit_report(f"Error: {e}")
            return False

    def _emit_report(self, *args):
        self.report.emit({"info": {"values": [{"message": arg} for arg in args]}})

    def _run_sh(self):
        self._emit_report("Getting auxiliary data from DB (1/5)...")
        self.setProgress(0)

        discount_rate = float(self.config_engine["drate"])
        break_growth_rate = float(self.config_engine["bratemain0"])

        last_leak_year = tools_db.get_rows(
            """
            select max(year) from (select 
                date_part('year', startdate) as year
                FROM asset.leaks) years
            """
        )[0][0]

        if self.isCanceled():
            self._emit_report("Task canceled.")
            return False
        self._emit_report("Getting pipe data from DB (2/5)...")
        self.setProgress(20)

        sql = """
            select a.arc_id,
                a.matcat_id,
                a.dnom,
                st_length(a.the_geom) length,
                coalesce(ai.rleak, 0) rleak, 
                a.expl_id,
                a.presszone_id,
                ai.plan,
                ai.social,
                ai.other
            from asset.arc_asset a 
            left join asset.arc_input ai using (arc_id)
        """
        filters = []
        if self.features:
            filters.append(f"""a.arc_id in ('{"','".join(self.features)}')""")
        if self.exploitation:
            filters.append(f"a.expl_id = {self.exploitation}")
        if self.presszone:
            filters.append(f"a.presszone_id = '{self.presszone}'")
        if self.diameter:
            filters.append(f"a.dnom = {self.diameter}")
        if self.material:
            filters.append(f"a.matcat_id = '{self.material}'")
        if filters:
            sql += f"where {' and '.join(filters)}"
        arcs = tools_db.get_rows(sql)
        if not arcs:
            self._emit_report(
                "Task canceled:", "No pipes to process with selected filters."
            )
            return False

        if self.isCanceled():
            self._emit_report("Task canceled.")
            return False
        self._emit_report("Calculating values (3/5)...")
        self.setProgress(40)

        output_arcs = []
        for arc in arcs:
            (
                arc_id,
                arc_material,
                arc_diameter,
                arc_length,
                rleak,
                expl_id,
                presszone_id,
                plan,
                social,
                other,
            ) = arc
            if (
                arc_diameter is None
                or arc_diameter <= 0
                or arc_diameter > max(self.config_diameter.keys())
            ):
                continue
            if arc_length is None:
                continue
            if self.exploitation and self.exploitation != expl_id:
                continue
            if self.presszone and self.presszone != presszone_id:
                continue
            if self.diameter and self.diameter != arc_diameter:
                continue
            if self.material and self.material != arc_material:
                continue

            reference_dnom = get_min_greater_than(
                self.config_diameter.keys(), arc_diameter
            )
            cost_repmain = self.config_diameter[reference_dnom]["cost_repmain"]

            replacement_cost = self.config_diameter[reference_dnom]["cost_constr"]
            cost_constr = replacement_cost * float(arc_length)

            material_compliance = 10
            if (
                arc_material in self.config_material
                and self.config_material[arc_material]
            ):
                material_compliance = self.config_material[arc_material]["compliance"]

            compliance = 10 - min(
                self.config_diameter[reference_dnom]["compliance"],
                material_compliance,
            )

            strategic = 10 if plan or social or other else 0

            if rleak == 0 or rleak is None:
                year = None
            else:
                year = int(
                    optimal_replacement_time(
                        last_leak_year,
                        float(rleak),
                        break_growth_rate,
                        cost_repmain,
                        replacement_cost * 1000,
                        discount_rate,
                    )
                )
            output_arcs.append(
                [
                    arc_id,
                    cost_repmain,
                    cost_constr,
                    break_growth_rate,
                    year,
                    compliance,
                    strategic,
                ]
            )
        if not len(output_arcs):
            self._emit_report(
                "Task canceled:", "No pipes to process with selected filters."
            )
            return False

        self.setProgress(50)

        years = [x[4] for x in output_arcs if x[4]]
        min_year = min(years) if years else None
        max_year = max(years) if years else None

        for arc in output_arcs:
            _, _, _, _, year, compliance, strategic = arc
            year_order = 0
            if max_year and min_year:
                year_order = 10 * (
                    1 - ((year or max_year) - min_year) / (max_year - min_year)
                )
            val = (
                year_order * self.config_engine["expected_year"]
                + compliance * self.config_engine["compliance"]
                + strategic * self.config_engine["strategic"]
            )
            arc.extend([year_order, val])

        if self.isCanceled():
            self._emit_report("Task canceled.")
            return False
        self._emit_report("Updating tables (4/5)...")
        self.setProgress(60)

        sql = f"select result_id from asset.cat_result where result_name = '{self.result_name}'"
        result_id = tools_db.get_row(sql)
        print(f"RESULT_ID 11 -> {result_id}")
        if result_id is not None:
            self._emit_report("This result name already exist.")
            return False

        str_features = (
            f"""ARRAY['{"','".join(self.features)}']""" if self.features else "NULL"
        )
        str_presszone_id = f"'{self.presszone}'" if self.presszone else "NULL"
        str_material_id = f"'{self.material}'" if self.material else "NULL"
        tools_db.execute_sql(
            f"""
            insert into asset.cat_result (result_name, 
                result_type, 
                descript,
                features,
                expl_id,
                presszone_id,
                dnom,
                material_id,
                budget,
                target_year,
                cur_user,
                tstamp)
            values ('{self.result_name}',
                '{self.result_type}',
                '{self.result_description}',
                {str_features},
                {self.exploitation or 'NULL'},
                {str_presszone_id},
                {self.diameter or 'NULL'},
                {str_material_id},
                NULL,
                NULL,
                current_user,
                now())
            """
        )

        self.setProgress(63)

        sql = f"select result_id from asset.cat_result where result_name = '{self.result_name}'"
        result_id = tools_db.get_row(sql)[0]

        config_diameter_fields = list(self.config_diameter.values())[0].keys()
        save_config_diameter_sql = f"""
            delete from asset.config_diameter where result_id = {result_id};
            insert into asset.config_diameter 
                (result_id, dnom, {','.join(config_diameter_fields)})
            values
        """
        for dnom, fields in self.config_diameter.items():
            save_config_diameter_sql += f"""
                ({result_id},{dnom},{','.join([str(fields[x]) for x in config_diameter_fields])}),
            """
        save_config_diameter_sql = save_config_diameter_sql.strip()[:-1]
        tools_db.execute_sql(save_config_diameter_sql)

        self.setProgress(66)

        config_material_fields = list(self.config_material.values())[0].keys()
        save_config_material_sql = f"""
            delete from asset.config_material where result_id = {result_id};
            insert into asset.config_material 
                (result_id, material, {','.join(config_material_fields)})
            values
        """
        for material, fields in self.config_material.items():
            save_config_material_sql += f"""
                ({result_id},'{material}',{','.join([str(fields[x]) for x in config_material_fields])}),
            """
        save_config_material_sql = save_config_material_sql.strip()[:-1]
        tools_db.execute_sql(save_config_material_sql)

        self.setProgress(69)

        save_config_engine_sql = f"""
            delete from asset.config_engine where result_id = {result_id};
            insert into asset.config_engine
                (result_id, parameter, value)
            values
        """
        for k, v in self.config_engine.items():
            save_config_engine_sql += f"({result_id}, '{k}', {v}),"
        save_config_engine_sql = save_config_engine_sql.strip()[:-1]
        tools_db.execute_sql(save_config_engine_sql)

        self.setProgress(72)

        tools_db.execute_sql(
            f"delete from asset.arc_engine_sh where result_id = {result_id};"
        )
        index = 0
        loop = 0
        ended = False
        while not ended:
            save_arcs_sql = f"""
                insert into asset.arc_engine_sh (
                    arc_id,
                    result_id,
                    cost_repmain,
                    cost_leak,
                    cost_constr,
                    bratemain,
                    year,
                    compliance,
                    strategic,
                    year_order,
                    val
                ) values 
            """
            for i in range(1000):
                try:
                    (
                        arc_id,
                        cost_repmain,
                        cost_constr,
                        break_growth_rate,
                        year,
                        compliance,
                        strategic,
                        year_order,
                        val,
                    ) = output_arcs[index]
                    save_arcs_sql += f"""
                        ({arc_id},
                        {result_id},
                        {cost_repmain},
                        {cost_repmain},
                        {cost_constr},
                        {break_growth_rate},
                        {year or 'NULL'},
                        {compliance},
                        {strategic},
                        {year_order},
                        {val}),
                    """
                    index += 1
                except IndexError:
                    ended = True
                    break
            save_arcs_sql = save_arcs_sql.strip()[:-1]
            tools_db.execute_sql(save_arcs_sql)
            loop += 1
            progress = (76 - 72) / len(output_arcs) * 1000 * loop + 72
            self.setProgress(progress)

        tools_db.execute_sql(
            f"""
            delete from asset.arc_output
                where result_id = {result_id};
            insert into asset.arc_output 
                    (arc_id, result_id, val, orderby, expected_year, budget, total, mandatory)
                select arc_id,
                    sh.result_id,
                    val,
                    rank() over (order by coalesce(i.mandatory, false) desc, val desc),
                    year,
                    cost_constr,
                    sum(cost_constr) over (order by coalesce(i.mandatory, false) desc, val desc, arc_id),
                    mandatory
                from asset.arc_engine_sh sh
                left join asset.arc_input i using (arc_id)
                where sh.result_id = {result_id}
                order by sum;
            """
        )

        if self.isCanceled():
            self._emit_report("Task canceled.")
            return False
        self._emit_report("Generating result stats (5/5)...")
        self.setProgress(80)

        invalid_diameters_count = tools_db.get_row(
            f"""
            select count(*)
            from asset.arc_asset
            where dnom is null 
                or dnom <= 0
                or dnom > (
                    select max(dnom)
                    from asset.config_diameter
                    where result_id = {result_id}
                )
            """
        )[0]

        invalid_diameters = []
        if invalid_diameters_count:
            invalid_diameters = [
                x[0]
                for x in tools_db.get_rows(
                    f"""
                    select distinct dnom
                    from asset.arc_asset
                    where dnom is null 
                        or dnom <= 0
                        or dnom > (
                            select max(dnom)
                            from asset.config_diameter
                            where result_id = {result_id}
                        )
                    """
                )
            ]

        invalid_materials_count = tools_db.get_row(
            f"""
            select count(*)
            from asset.arc_asset a
            where not exists (
                select 1
                from asset.config_material
                where 
                    material = a.matcat_id
                    and result_id = {result_id}
            )
            """
        )[0]

        invalid_materials = []
        if invalid_materials_count:
            invalid_materials = [
                x[0]
                for x in tools_db.get_rows(
                    f"""
                    select distinct matcat_id
                    from asset.arc_asset a
                    where not exists (
                        select 1
                        from asset.config_material
                        where 
                            material = a.matcat_id
                            and result_id = {result_id}
                    )
                    """
                )
            ]

        if self.isCanceled():
            self._emit_report("Task canceled.")
            return False

        self._emit_report(
            "Task finished!",
            "Warnings:" if invalid_diameters_count or invalid_materials_count else "",
        )

        if invalid_diameters_count:
            self._emit_report(
                f"Pipes with invalid diameters: {invalid_diameters_count}.",
                f"Invalid diameters: {', '.join(map(lambda x: 'NULL' if x is None else str(x), invalid_diameters))}.",
                "These pipes WERE NOT assigned a priority value.",
            )

        if invalid_materials_count:
            self._emit_report(
                f"Pipes with invalid materials: {invalid_materials_count}.",
                f"Invalid materials: {', '.join(map(lambda x: 'NULL' if x is None else str(x), invalid_materials))}.",
                "These pipes were assigned as compliant by default, "
                + "which may result in a lower priority value.",
            )

        return True

    def _run_wm(self):
        pass
