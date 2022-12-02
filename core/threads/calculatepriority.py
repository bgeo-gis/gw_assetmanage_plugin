from math import log, log1p, exp

from qgis.core import QgsTask
from qgis.PyQt.QtCore import pyqtSignal

from .task import GwTask
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

    def __init__(self, description, result_name, result_description, exploitation, budget, target_year):
        super().__init__(description, QgsTask.CanCancel)
        self.result_name = result_name
        self.result_description = result_description
        self.result_exploitation = exploitation
        self.result_budget = budget
        self.result_target_year = target_year


    def run(self):
        try:
            self._emit_report("Getting config data from DB (1/5)...")
            self.setProgress(0)

            sql = (
                "select parameter, value::float, active "
                + "from asset.config_engine "
                + "where method = 'S-H' "
            )
            rows = tools_db.get_rows(sql)
            config_engine = {}
            for row in rows:
                parameter, value, _ = row
                config_engine[parameter] = value
            discount_rate = float(config_engine["drate"])
            break_growth_rate = float(config_engine["bratemain0"])

            rows = tools_db.get_rows(
                """
                select dnom, cost_constr, cost_repmain, compliance
                    from asset.config_diameter
                """
            )
            diameters = {}
            for row in rows:
                dnom, cost_constr, cost_repmain, compliance = row
                diameters[int(dnom)] = {
                    "replacement_cost": float(cost_constr),
                    "repairing_cost": float(cost_repmain),
                    "compliance": compliance,
                }

            rows = tools_db.get_rows(
                """
                select material, compliance
                    from asset.config_material
                """
            )
            materials = {}
            for row in rows:
                material, compliance = row
                materials[material] = compliance

            last_leak_year = tools_db.get_rows(
                """
                select max(year) from (select 
                    date_part('year', to_date(startdate, 'DD/MM/YYYY')) as year
                    FROM asset.leaks) years
                """
            )[0][0]

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False
            self._emit_report("Getting pipe data from DB (2/5)...")
            self.setProgress(20)

            sql = (
                "select a.arc_id, a.matcat_id, a.dnom, "
                + "st_length(a.the_geom) length, coalesce(ai.rleak, 0) rleak "
                + "from asset.arc_asset a "
                + "left join asset.arc_input ai "
                + "on (a.arc_id = ai.arc_id and ai.result_id = 0) "
            )
            arcs = tools_db.get_rows(sql)

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False
            self._emit_report("Calculating values (3/5)...")
            self.setProgress(40)

            sql = (
                f"select result_id from asset.cat_result where result_name = '{self.result_name}'"
            )
            result_id = tools_db.get_row(sql)
            print(f"RESULT_ID 11 -> {result_id}")
            if result_id is not None:
                self._emit_report("This result name already exist.")
                return False

            tools_db.execute_sql(
                f"""
                insert into asset.cat_result (result_name, result_type, descript, expl_id, budget, target_year, cur_user, tstamp)
                values ('{self.result_name}', 'GLOBAL', '{self.result_description}', '{self.result_exploitation}', '{self.result_budget}', '{self.result_target_year}', current_user, now())
                """)
            sql = (
                    f"select id from asset.cat_result where result_name = '{self.result_name}'"
            )
            result_id = tools_db.get_row(sql)

            save_arcs_sql = f"""
                delete from asset.arc_engine_sh where result_id = {result_id[0]};
                insert into asset.arc_engine_sh 
                (arc_id, result_id, cost_repmain, cost_leak, cost_constr, bratemain, year, compliance)
                values 
            """

            for arc in arcs:
                arc_id, arc_material, arc_diameter, arc_length, rleak = arc
                if (
                    arc_diameter is None
                    or arc_diameter <= 0
                    or arc_diameter > max(diameters.keys())
                ):
                    continue
                if arc_length is None:
                    continue
                reference_dnom = get_min_greater_than(diameters.keys(), arc_diameter)
                cost_repmain = diameters[reference_dnom]["repairing_cost"]

                replacement_cost = diameters[reference_dnom]["replacement_cost"]
                cost_constr = replacement_cost * float(arc_length)

                material_compliance = True
                if arc_material in materials and materials[arc_material]:
                    material_compliance = materials[arc_material]

                compliance = (
                    0
                    if diameters[reference_dnom]["compliance"] and material_compliance
                    else 10
                )

                if rleak == 0 or rleak is None:
                    year = "NULL"
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
                save_arcs_sql += f"({arc_id},{result_id[0]},{cost_repmain},{cost_repmain},{cost_constr},{break_growth_rate},{year},{compliance}),"

            save_arcs_sql = save_arcs_sql[:-1]

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False
            self._emit_report("Updating tables (4/5)...")
            self.setProgress(60)
            print(f"QUERY INSERT -> {save_arcs_sql}")
            tools_db.execute_sql(save_arcs_sql)
            print(f"UPDATE -> ")
            print(f"""
                update asset.arc_engine_sh 
                    set year_order = 10 * (1 - (coalesce(year, years.max) - years.min) / years.difference::real)
                    from (
                        select min(year), max(year), max(year) - min(year) difference from asset.arc_engine_sh
                        ) as years
                    where result_id = {result_id[0]};
                update asset.arc_engine_sh sh
                    set val = sh.year_order * weight.year_order + sh.compliance * weight.compliance
                    from (
                        select y.value::real year_order, c.value::real compliance
                            from asset.config_engine y
                            join asset.config_engine c on c.parameter = 'compliance'
                            where y.parameter = 'expected_year'
                    ) as weight
                    where result_id = {result_id[0]};
                delete from asset.arc_output
                    where result_id = {result_id[0]};
                insert into asset.arc_output (arc_id, result_id, val, expected_year, budget)
                    select arc_id, result_id, val, year, cost_constr
                        from asset.arc_engine_sh
                        where result_id = {result_id[0]};
                """)
            tools_db.execute_sql(
                f"""
                update asset.arc_engine_sh 
                    set year_order = 10 * (1 - (coalesce(year, years.max) - years.min) / years.difference::real)
                    from (
                        select min(year), max(year), max(year) - min(year) difference from asset.arc_engine_sh
                        ) as years
                    where result_id = {result_id[0]};
                update asset.arc_engine_sh sh
                    set val = sh.year_order * weight.year_order + sh.compliance * weight.compliance
                    from (
                        select y.value::real year_order, c.value::real compliance
                            from asset.config_engine y
                            join asset.config_engine c on c.parameter = 'compliance'
                            where y.parameter = 'expected_year'
                    ) as weight
                    where result_id = {result_id[0]};
                delete from asset.arc_output
                    where result_id = {result_id[0]};
                insert into asset.arc_output (arc_id, result_id, val, expected_year, budget)
                    select arc_id, result_id, val, year, cost_constr
                        from asset.arc_engine_sh
                        where result_id = {result_id[0]};
                """
            )

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False
            self._emit_report("Generating result stats (5/5)...")
            self.setProgress(80)

            invalid_diameters_count = tools_db.get_rows(
                """
                select count(*)
                from asset.arc_asset
                where dnom is null 
                    or dnom <= 0
                    or dnom > (select max(dnom) from asset.config_diameter)
                """
            )[0][0]

            invalid_diameters = [
                x[0]
                for x in tools_db.get_rows(
                    """
                    select distinct dnom
                    from asset.arc_asset
                    where dnom is null 
                        or dnom <= 0
                        or dnom > (select max(dnom) from asset.config_diameter)
                    """
                )
            ]

            invalid_materials_count = tools_db.get_rows(
                """
                select count(*)
                from asset.arc_asset a
                where not exists (
                    select 1
                    from asset.config_material
                    where material = a.matcat_id
                )
                """
            )[0][0]

            invalid_materials = [
                x[0]
                for x in tools_db.get_rows(
                    """
                    select distinct matcat_id
                    from asset.arc_asset a
                    where not exists (
                        select 1
                        from asset.config_material
                        where material = a.matcat_id
                    )
                    """
                )
            ]

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False

            self._emit_report(
                "Task finished!",
                "Warnings:"
                if invalid_diameters_count or invalid_materials_count
                else "",
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

        except Exception as e:
            self._emit_report(f"Error: {e}")
            return False

    def _emit_report(self, *args):
        self.report.emit({"info": {"values": [{"message": arg} for arg in args]}})
