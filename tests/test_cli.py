import pytest

from dicomplan.config_parser import parse_arguments, get_model_from_args


# ---------------------------------------------------------------------------
# parse_arguments
# ---------------------------------------------------------------------------

class TestParseArguments:
    def test_square_defaults(self):
        args = parse_arguments(["square", "10", "10"])
        assert args.pattern_type == "square"
        assert args.dx == 10.0
        assert args.dy == 10.0

    def test_square_custom_spacing(self):
        args = parse_arguments(["square", "5", "5", "--spacing", "1.0"])
        assert args.spacing == 1.0

    def test_square_hex_flag(self):
        args = parse_arguments(["square", "5", "5", "--hex"])
        assert args.hex is True

    def test_circle_defaults(self):
        args = parse_arguments(["circle", "10"])
        assert args.pattern_type == "circle"
        assert args.diameter == 10.0

    def test_circle_with_offset(self):
        args = parse_arguments(["circle", "10", "--xoffset", "1.5", "--yoffset", "-2.0"])
        assert args.xoffset == 1.5
        assert args.yoffset == -2.0

    def test_version_exits(self):
        with pytest.raises(SystemExit) as exc:
            parse_arguments(["--version"])
        assert exc.value.code == 0

    def test_missing_subcommand_exits(self):
        with pytest.raises(SystemExit):
            parse_arguments([])

    def test_boost_rim_default(self):
        args = parse_arguments(["square", "10", "10"])
        assert args.boost_rim == 1.0

    def test_boost_rim_custom(self):
        args = parse_arguments(["square", "10", "10", "--boost_rim", "2.5"])
        assert args.boost_rim == 2.5


# ---------------------------------------------------------------------------
# get_model_from_args
# ---------------------------------------------------------------------------

class TestGetModelFromArgs:
    def test_square_model_shape(self):
        args = parse_arguments(["square", "10", "8"])
        model = get_model_from_args(args)
        assert model.spot_shape == "square"
        assert model.spot_xymin == [-5.0, -4.0]
        assert model.spot_xymax == [5.0, 4.0]

    def test_square_hex_pattern_type(self):
        args = parse_arguments(["square", "10", "10", "--hex"])
        model = get_model_from_args(args)
        assert model.spot_pattern_type == "hexagonal"

    def test_circle_model_shape(self):
        args = parse_arguments(["circle", "12"])
        model = get_model_from_args(args)
        assert model.spot_shape == "circle"
        assert model.spot_diameter == 12.0

    def test_circle_offset_applied(self):
        args = parse_arguments(["circle", "10", "--xoffset", "1.0", "--yoffset", "2.0"])
        model = get_model_from_args(args)
        assert model.spot_center == [1.0, 2.0]

    def test_square_offset_applied(self):
        args = parse_arguments(["square", "10", "10", "--xoffset", "1.0"])
        model = get_model_from_args(args)
        assert model.spot_xymin[0] == pytest.approx(-4.0)
        assert model.spot_xymax[0] == pytest.approx(6.0)

    def test_boost_rim_not_set_when_default(self):
        args = parse_arguments(["square", "10", "10"])
        model = get_model_from_args(args)
        assert model.boost_rim == 1.0

    def test_boost_rim_set_when_above_one(self):
        args = parse_arguments(["square", "10", "10", "--boost_rim", "2.0"])
        model = get_model_from_args(args)
        assert model.boost_rim == 2.0

    def test_patient_fields(self):
        args = parse_arguments(["-pn", "Doe^John", "-pi", "12345", "square", "10", "10"])
        model = get_model_from_args(args)
        assert model.plan_patient_name == "Doe^John"
        assert model.plan_patient_id == "12345"


# ---------------------------------------------------------------------------
# CLI integration (main)
# ---------------------------------------------------------------------------

class TestCLIIntegration:
    def test_square_writes_dicom(self, tmp_path):
        from dicomplan.main import main
        output = tmp_path / "test_square.dcm"
        main(["-o", str(output), "square", "5", "5"])
        assert output.exists()
        assert output.stat().st_size > 0

    def test_circle_writes_dicom(self, tmp_path):
        from dicomplan.main import main
        output = tmp_path / "test_circle.dcm"
        main(["-o", str(output), "circle", "10"])
        assert output.exists()
        assert output.stat().st_size > 0
