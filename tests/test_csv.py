from collections.abc import Iterable

import pytest

from dicomplan.config_parser import get_model_from_args, parse_arguments
from dicomplan.dicom import Dicom
from dicomplan.spots import (_dose_plot_extent, generate_csv_layers,
                             generate_csv_pattern, generate_spot_layers)


class TestParseArgumentsCsv:
    def test_csv_required_args(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        args = parse_arguments(["csv", str(csv_path)])
        assert args.pattern_type == "csv"
        assert args.csv_path == str(csv_path)

    def test_csv_rejects_mu_per_spot(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        with pytest.raises(SystemExit):
            parse_arguments(["csv", str(csv_path), "--mu-per-spot", "2"])


class TestGetModelFromArgsCsv:
    def test_csv_model_shape_and_absolute_mu(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        args = parse_arguments(["csv", str(csv_path)])
        model = get_model_from_args(args)
        assert model.spot_shape == "csv"
        assert model.spot_csv_path == str(csv_path)
        assert model.spot_mu is None
        assert model.spot_weights_are_absolute_mu is True

    def test_csv_offset_is_stored_for_spot_list(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        args = parse_arguments(["csv", str(csv_path), "--xoffset", "1.5", "--yoffset", "-2.0"])
        model = get_model_from_args(args)
        assert model.spot_offset == [1.5, -2.0]
        assert model.spot_xymin == [0.0, 0.0]
        assert model.spot_xymax == [0.0, 0.0]


class TestGenerateCsvPattern:
    def test_reads_csv_spots_with_absolute_mu_and_offset(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        csv_path.write_text("x,y,mu\n1.0,2.0,3.0\n-1.5,0.5,4.5\n")
        args = parse_arguments(["csv", str(csv_path), "--xoffset", "0.5", "--yoffset", "-1.0"])
        model = get_model_from_args(args)

        coords, weights = generate_csv_pattern(model)

        assert coords == pytest.approx([1.5, 1.0, -1.0, -0.5])
        assert weights == pytest.approx([3.0, 4.5])

    def test_requires_x_y_and_mu_columns(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        csv_path.write_text("x,y\n1.0,2.0\n")
        args = parse_arguments(["csv", str(csv_path)])
        model = get_model_from_args(args)

        with pytest.raises(ValueError, match="mu"):
            generate_csv_pattern(model)


class TestCsvDicomIntegration:
    def test_csv_mu_values_are_not_scaled_by_mu_per_spot(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        csv_path.write_text("x,y,mu\n1.0,2.0,2.5\n-1.0,0.5,7.5\n")
        args = parse_arguments(["csv", str(csv_path), "--xoffset", "1.0", "--yoffset", "-2.0"])
        model = get_model_from_args(args)

        dicom = Dicom()
        dicom.apply_model(model)

        first_control_point = dicom.ds.IonBeamSequence[0].IonControlPointSequence[0]
        assert first_control_point.ScanSpotMetersetWeights == pytest.approx([2.5, 7.5])
        assert first_control_point.ScanSpotPositionMap == pytest.approx([20.0, 0.0, 0.0, -15.0])
        assert dicom.ds.FractionGroupSequence[0].ReferencedBeamSequence[0].BeamMeterset == pytest.approx(10.0)
        assert dicom.ds.IonBeamSequence[0].FinalCumulativeMetersetWeight == pytest.approx(10.0)


class TestCsvDosePlot:
    def test_plot_extent_covers_all_spots(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        csv_path.write_text("x,y,mu\n-3.0,-3.0,10\n3.0,2.0,10\n0.0,0.0,5\n")
        args = parse_arguments(["csv", str(csv_path)])
        model = get_model_from_args(args)

        coords, _ = generate_csv_pattern(model)

        assert _dose_plot_extent(coords) == pytest.approx((-4.0, 4.0, -4.0, 3.0))

    def test_dose_plot_is_written_for_csv_spots(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        csv_path.write_text("x,y,mu\n-3.0,-3.0,10\n3.0,3.0,10\n")
        plot_path = tmp_path / "plot_dose.png"
        args = parse_arguments(["--dose_plot", "--dose_plot_filepath", str(plot_path),
                                "csv", str(csv_path)])
        model = get_model_from_args(args)

        generate_spot_layers(model)

        assert plot_path.exists()


class TestCsvEnergyLayers:
    def test_single_layer_without_energy_column(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        csv_path.write_text("x,y,mu\n1.0,2.0,3.0\n-1.0,0.5,4.0\n")
        args = parse_arguments(["csv", str(csv_path), "--energy", "175"])
        model = get_model_from_args(args)

        layers = generate_csv_layers(model)

        assert len(layers) == 1
        assert layers[0].energy == 175.0
        assert layers[0].nspots == 2

    def test_energy_change_starts_a_new_layer(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        csv_path.write_text("x,y,mu,energy\n"
                            "-1.0,-1.0,10.0,100.0\n"
                            "1.0,-1.0,10.0,100.0\n"
                            "-1.0,1.0,20.0,120.0\n"
                            "0.0,0.0,30.0,120.0\n"
                            "0.0,2.0,5.0,150.0\n")
        args = parse_arguments(["csv", str(csv_path)])
        model = get_model_from_args(args)

        layers = generate_csv_layers(model)

        assert [layer.energy for layer in layers] == [100.0, 120.0, 150.0]
        assert [layer.nspots for layer in layers] == [2, 2, 1]
        assert layers[1].coords == pytest.approx([-1.0, 1.0, 0.0, 0.0])
        assert layers[1].weights == pytest.approx([20.0, 30.0])

    def test_offset_applies_to_every_layer(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        csv_path.write_text("x,y,mu,energy\n0.0,0.0,1.0,100.0\n0.0,0.0,1.0,120.0\n")
        args = parse_arguments(["csv", str(csv_path), "--xoffset", "1.0", "--yoffset", "-2.0"])
        model = get_model_from_args(args)

        layers = generate_csv_layers(model)

        assert layers[0].coords == pytest.approx([1.0, -2.0])
        assert layers[1].coords == pytest.approx([1.0, -2.0])

    def test_descending_energy_is_rejected(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        csv_path.write_text("x,y,mu,energy\n0.0,0.0,1.0,150.0\n1.0,1.0,1.0,100.0\n")
        args = parse_arguments(["csv", str(csv_path)])
        model = get_model_from_args(args)

        with pytest.raises(ValueError, match="ascending energy order"):
            generate_csv_layers(model)

    def test_repeated_energy_further_down_is_rejected(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        csv_path.write_text("x,y,mu,energy\n0.0,0.0,1.0,100.0\n1.0,1.0,1.0,150.0\n2.0,2.0,1.0,100.0\n")
        args = parse_arguments(["csv", str(csv_path)])
        model = get_model_from_args(args)

        with pytest.raises(ValueError, match="ascending energy order"):
            generate_csv_layers(model)

    def test_non_numeric_energy_is_rejected(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        csv_path.write_text("x,y,mu,energy\n0.0,0.0,1.0,abc\n")
        args = parse_arguments(["csv", str(csv_path)])
        model = get_model_from_args(args)

        with pytest.raises(ValueError, match="numeric x, y, mu and energy"):
            generate_csv_layers(model)

    def test_dose_plot_covers_all_layers(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        csv_path.write_text("x,y,mu,energy\n-3.0,0.0,1.0,100.0\n3.0,0.0,1.0,120.0\n")
        args = parse_arguments(["csv", str(csv_path)])
        model = get_model_from_args(args)

        coords, weights = generate_csv_pattern(model)

        assert coords == pytest.approx([-3.0, 0.0, 3.0, 0.0])
        assert _dose_plot_extent(coords) == pytest.approx((-4.0, 4.0, -1.0, 1.0))


def _as_list(value):
    """A DICOM element holding a single value comes back as a scalar, not a one-item list."""
    return list(value) if isinstance(value, Iterable) else [value]


class TestCsvEnergyLayersDicom:
    def _plan(self, tmp_path):
        csv_path = tmp_path / "spots.csv"
        csv_path.write_text("x,y,mu,energy\n"
                            "-1.0,-1.0,10.0,100.0\n"
                            "1.0,-1.0,10.0,100.0\n"
                            "-1.0,1.0,20.0,120.0\n"
                            "0.0,0.0,30.0,120.0\n"
                            "0.0,2.0,5.0,150.0\n")
        args = parse_arguments(["csv", str(csv_path)])
        dicom = Dicom()
        dicom.apply_model(get_model_from_args(args))
        return dicom

    def test_one_control_point_pair_per_layer(self, tmp_path):
        ib = self._plan(tmp_path).ds.IonBeamSequence[0]

        assert ib.NumberOfControlPoints == 6
        assert len(ib.IonControlPointSequence) == 6
        assert [cp.ControlPointIndex for cp in ib.IonControlPointSequence] == [0, 1, 2, 3, 4, 5]

    def test_both_control_points_of_a_pair_share_energy_and_positions(self, tmp_path):
        cps = self._plan(tmp_path).ds.IonBeamSequence[0].IonControlPointSequence

        assert [cp.NominalBeamEnergy for cp in cps] == [100.0, 100.0, 120.0, 120.0, 150.0, 150.0]
        assert [cp.NumberOfScanSpotPositions for cp in cps] == [2, 2, 2, 2, 1, 1]
        for even, odd in zip(cps[::2], cps[1::2]):
            assert list(even.ScanSpotPositionMap) == list(odd.ScanSpotPositionMap)

    def test_only_even_control_points_carry_weights(self, tmp_path):
        cps = self._plan(tmp_path).ds.IonBeamSequence[0].IonControlPointSequence

        assert cps[0].ScanSpotMetersetWeights == pytest.approx([10.0, 10.0])
        assert cps[2].ScanSpotMetersetWeights == pytest.approx([20.0, 30.0])
        assert _as_list(cps[4].ScanSpotMetersetWeights) == pytest.approx([5.0])
        for odd in cps[1::2]:
            assert _as_list(odd.ScanSpotMetersetWeights) == pytest.approx([0.0] * odd.NumberOfScanSpotPositions)

    def test_meterset_accumulates_across_layers(self, tmp_path):
        ds = self._plan(tmp_path).ds
        ib = ds.IonBeamSequence[0]
        cps = ib.IonControlPointSequence

        assert [cp.CumulativeMetersetWeight for cp in cps] == pytest.approx([0.0, 20.0, 20.0, 70.0, 70.0, 75.0])
        assert ib.FinalCumulativeMetersetWeight == pytest.approx(75.0)
        assert ds.FractionGroupSequence[0].ReferencedBeamSequence[0].BeamMeterset == pytest.approx(75.0)

    def test_dose_reference_coefficient_ramps_to_one(self, tmp_path):
        cps = self._plan(tmp_path).ds.IonBeamSequence[0].IonControlPointSequence
        coefficients = [cp.ReferencedDoseReferenceSequence[0].CumulativeDoseReferenceCoefficient for cp in cps]

        assert coefficients[0] == pytest.approx(0.0)
        assert coefficients[-1] == pytest.approx(1.0)
        assert coefficients == sorted(coefficients)

    def test_geometry_tags_only_on_the_first_control_point(self, tmp_path):
        cps = self._plan(tmp_path).ds.IonBeamSequence[0].IonControlPointSequence

        assert 'GantryAngle' in cps[0]
        assert 'SnoutPosition' in cps[0]
        for cp in cps[1:]:
            assert 'GantryAngle' not in cp
            assert 'SnoutPosition' not in cp
