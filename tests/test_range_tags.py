import struct

import pytest

from dicomplan.config_parser import get_model_from_args, parse_arguments
from dicomplan.dicom import Dicom, range_in_water_mm


# (nominal energy, (300b,1017)) read out of ../dicomfix/res/Plan5.5.dcm and PlanMono.dcm,
# two plans the treatment console accepted.
REFERENCE_RANGES = [
    (106.483, 85.3427), (103.183, 80.7252), (99.883, 76.2153), (96.583, 71.8145),
    (93.283, 67.4354), (89.983, 63.2636), (86.683, 59.2059), (83.383, 55.2640),
    (160.000, 174.6501),
]


class TestRangeInWater:
    @pytest.mark.parametrize("energy,expected", REFERENCE_RANGES)
    def test_matches_the_reference_plans(self, energy, expected):
        assert range_in_water_mm(energy) == pytest.approx(expected, rel=2e-3)

    def test_matches_the_textbook_bragg_kleeman_curve(self):
        # R[cm] = 0.0022 * E^1.77 for water, i.e. 10x that in mm
        for energy in (80.0, 120.0, 180.0, 243.0):
            assert range_in_water_mm(energy) == pytest.approx(0.0022 * energy ** 1.77 * 10, rel=5e-3)


def _unpack(element):
    return struct.unpack('<f', element.value)[0]


class TestPrivateRangeTags:
    def _plan(self, tmp_path, rows):
        csv_path = tmp_path / "spots.csv"
        csv_path.write_text("x,y,mu,energy\n" + "".join(rows))
        dicom = Dicom()
        dicom.apply_model(get_model_from_args(parse_arguments(["csv", str(csv_path)])))
        return dicom.ds

    def test_each_layer_carries_the_range_of_its_own_energy(self, tmp_path):
        ds = self._plan(tmp_path, ["0.0,0.0,1.0,243.1\n", "0.0,0.0,1.0,219.2\n"])
        cps = ds.IonBeamSequence[0].IonControlPointSequence

        assert _unpack(cps[0][0x300b, 0x1017]) == pytest.approx(range_in_water_mm(243.1), rel=1e-6)
        assert _unpack(cps[2][0x300b, 0x1017]) == pytest.approx(range_in_water_mm(219.2), rel=1e-6)
        # the terminator repeats its layer's range
        assert _unpack(cps[1][0x300b, 0x1017]) == pytest.approx(_unpack(cps[0][0x300b, 0x1017]))

    def test_modulation_is_the_range_span(self, tmp_path):
        ds = self._plan(tmp_path, ["0.0,0.0,1.0,243.1\n", "0.0,0.0,1.0,219.2\n"])
        expected = range_in_water_mm(243.1) - range_in_water_mm(219.2)

        assert _unpack(ds.IonBeamSequence[0][0x300b, 0x100e]) == pytest.approx(expected, rel=1e-6)

    def test_single_layer_plan_is_unmodulated(self, tmp_path):
        # PlanMono.dcm, a single-layer plan the console accepted, carries 0.0 here.
        ds = self._plan(tmp_path, ["0.0,0.0,1.0,160.0\n"])

        assert _unpack(ds.IonBeamSequence[0][0x300b, 0x100e]) == pytest.approx(0.0)

    def test_geometric_patterns_also_get_their_range(self, tmp_path):
        dicom = Dicom()
        dicom.apply_model(get_model_from_args(parse_arguments(["square", "4", "4", "--energy", "200"])))
        cp = dicom.ds.IonBeamSequence[0].IonControlPointSequence[0]

        assert _unpack(cp[0x300b, 0x1017]) == pytest.approx(range_in_water_mm(200.0), rel=1e-6)
