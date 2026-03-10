from typing import Optional


class PlanInputModel:
    def __init__(self, plan_id: str, plan_name: str, plan_description: str):

        # these are model.py only, will not be passed to dicom
        self.plan_id = plan_id
        self.plan_name = plan_name
        self.plan_description = plan_description

        # these are passed to dicom
        self.output_path: Optional[str] = None
        self.plan_label: Optional[str] = None
        self.plan_patient_name: Optional[str] = None
        self.plan_patient_id: Optional[str] = None
        self.plan_reviewer_name: Optional[str] = None
        self.plan_operator_name: Optional[str] = None
        self.field_treatment_machine: Optional[str] = None
        self.field_gantry_angle: Optional[float] = None
        self.field_table_position: Optional[list[float]] = None  # cm
        self.field_snout_position: Optional[float] = None  # cm

        self.spot_spacing: Optional[float] = None

        # position data with offsets
        # only for square patterns
        self.spot_xymin: list[float] = [0.0, 0.0]  # cm
        self.spot_xymax: list[float] = [0.0, 0.0]  # cm
        self.spot_shape: Optional[str] = None
        self.trim_corners: bool = False

        # only for circular patterns
        self.spot_diameter = 10.0  # cm
        self.spot_center = [0.0, 0.0]  # cm
        self.spot_count = None

        self.spot_energy: float = 0.0  # MeV
        self.spot_mu: Optional[float] = None
        self.spot_shape: Optional[str] = None  # circular, square, or image
        self.spot_pattern_type: Optional[str] = None  # square or hexagonal

        # in case of user loads a png image, this will be the path to the image
        self.spot_image_path: Optional[str] = None

        self.plot_dose: bool = False

        # sigma to fwhm conversion: fwhm = 2.355 * sigma

        self.plot_dose_fwhm = [0.893, 0.615]  # cm, full width at half maximum for dose plot
        self.plot_dose_filepath = "plot_dose.png"
