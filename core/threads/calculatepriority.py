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
    BREAKS_YEAR_0 = 0.2
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

    def __init__(self, description, result_name, result_description):
        super().__init__(description, QgsTask.CanCancel)
        self.result_name = result_name
        self.result_description = result_description

    def run(self):
        try:
            # FIXME: Number of steps and progress
            self._emit_report("Getting config data from DB (1/n)...")
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

            sql = (
                "select dnom, cost_constr, cost_repmain, compliance "
                + "from asset.config_diameter "
            )
            rows = tools_db.get_rows(sql)
            diameters = {}
            for row in rows:
                dnom, cost_constr, cost_repmain, _ = row
                diameters[int(dnom)] = {
                    "replacement_cost": float(cost_constr),
                    "repairing_cost": float(cost_repmain),
                }

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
            self._emit_report("Getting pipe data from DB (2/n)...")
            self.setProgress(10)

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
            self._emit_report("Calculating values (3/n)...")
            self.setProgress(20)

            save_arcs_sql = """
                delete from asset.arc_engine_sh where result_id = 0;
                insert into asset.arc_engine_sh 
                (arc_id, result_id, cost_repmain, cost_leak, cost_constr, bratemain, year)
                values 
            """

            for arc in arcs:
                arc_id, _, arc_diameter, arc_length, rleak = arc
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
                save_arcs_sql += f"({arc_id},0,{cost_repmain},{cost_repmain},{cost_constr},{break_growth_rate},{year}),"

            save_arcs_sql = save_arcs_sql[:-1]

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False
            self._emit_report("Updating tables (4/n)...")
            self.setProgress(20)

            tools_db.execute_sql(save_arcs_sql)
            tools_db.execute_sql(
                """
                update asset.arc_engine_sh 
                    set year_order = 10 * (1 - (coalesce(year, years.max) - years.min) / years.difference::real)
                    from (
                        select min(year), max(year), max(year) - min(year) difference from asset.arc_engine_sh
                        ) as years
                    where result_id = 0;
                update asset.arc_engine_sh
                    set val = year_order
                    where result_id = 0;
                delete from asset.arc_output
                    where result_id = 0;
                insert into asset.arc_output (arc_id, result_id, val, expected_year, budget)
                    select arc_id, result_id, val, year, cost_constr
                        from asset.arc_engine_sh
                        where result_id = 0;
                """
            )

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False

            return True

        except Exception as e:
            self._emit_report(f"Error: {e}")
            return False

    def _emit_report(self, *args):
        self.report.emit({"info": {"values": [{"message": arg} for arg in args]}})
