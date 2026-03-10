import pytest
from pathlib import Path

from dicomplan.config_parser import parse_arguments, get_model_from_args

RES_DIR = Path(__file__).parent.parent / "res"
IMG = RES_DIR / "img.png"
IMG2 = RES_DIR / "img2.png"


# ---------------------------------------------------------------------------
# parse_arguments - image subcommand
# ---------------------------------------------------------------------------

class TestParseArgumentsImage:
    def test_image_required_args(self):
        args = parse_arguments(["image", "10", "10", str(IMG)])
        assert args.pattern_type == "image"
        assert args.width == 10.0
        assert args.height == 10.0
        assert args.image_path == str(IMG)

    def test_image_defaults(self):
        args = parse_arguments(["image", "10", "10", str(IMG)])
        assert args.spacing == 0.5
        assert args.mu_per_spot == 10.0
        assert args.energy == 120.0

    def test_image_custom_spacing(self):
        args = parse_arguments(["image", "10", "10", str(IMG), "--spacing", "1.0"])
        assert args.spacing == 1.0

    def test_image_with_offset(self):
        args = parse_arguments(["image", "10", "10", str(IMG), "--xoffset", "2.0", "--yoffset", "-1.5"])
        assert args.xoffset == 2.0
        assert args.yoffset == -1.5


# ---------------------------------------------------------------------------
# get_model_from_args - image pattern
# ---------------------------------------------------------------------------

class TestGetModelFromArgsImage:
    def test_image_model_shape(self):
        args = parse_arguments(["image", "10", "8", str(IMG)])
        model = get_model_from_args(args)
        assert model.spot_shape == "image"
        assert model.spot_image_path == str(IMG)

    def test_image_model_bounds(self):
        args = parse_arguments(["image", "10", "8", str(IMG)])
        model = get_model_from_args(args)
        assert model.spot_xymin == pytest.approx([-5.0, -4.0])
        assert model.spot_xymax == pytest.approx([5.0, 4.0])

    def test_image_offset_applied(self):
        args = parse_arguments(["image", "10", "10", str(IMG), "--xoffset", "1.0", "--yoffset", "2.0"])
        model = get_model_from_args(args)
        assert model.spot_xymin == pytest.approx([-4.0, -3.0])
        assert model.spot_xymax == pytest.approx([6.0, 7.0])


# ---------------------------------------------------------------------------
# CLI integration - image pattern writes DICOM
# ---------------------------------------------------------------------------

class TestCLIIntegrationImage:
    def test_img_writes_dicom(self, tmp_path):
        from dicomplan.main import main
        output = tmp_path / "test_image.dcm"
        main(["-o", str(output), "image", "10", "10", str(IMG)])
        assert output.exists()
        assert output.stat().st_size > 0

    def test_img2_writes_dicom(self, tmp_path):
        from dicomplan.main import main
        output = tmp_path / "test_image2.dcm"
        main(["-o", str(output), "image", "10", "10", str(IMG2)])
        assert output.exists()
        assert output.stat().st_size > 0

    def test_image_custom_spacing(self, tmp_path):
        from dicomplan.main import main
        output = tmp_path / "test_image_spacing.dcm"
        main(["-o", str(output), "image", "10", "10", str(IMG), "--spacing", "1.0"])
        assert output.exists()
        assert output.stat().st_size > 0
