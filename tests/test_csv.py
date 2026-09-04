import pytest

from dicomplan.config_parser import get_model_from_args, parse_arguments
from dicomplan.dicom import Dicom
from dicomplan.spots import generate_csv_pattern


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
