import argparse
from dicomplan.__version__ import __version__

from dicomplan.model import PlanInputModel

DEFAULT_SPOT_SPACING = 0.5  # cm
DEFAULT_MU_PER_SPOT = 10.0  # MU
DEFAULT_ENERGY = 120.0  # MeV
DEFAULT_FIELD_WIDTH = 10.0  # cm
DEFAULT_FIELD_HEIGHT = 10.0  # cm
DEFAULT_FIELD_DIAMETER = 10.0  # cm
DEFAULT_FWHMS = "1.000,1.000"  # cm, default FWHM for dose plot Gaussian kernel, as two values for x and y (e.g. "0.893,0.615")


def parse_arguments(args=None):
    """
    """
    parser = argparse.ArgumentParser(
        description='Create simple ECLIPSE DICOM proton therapy treatment plans.')

    parser.add_argument('-o', '--output', type=str, default="output.dcm",
                        help='Path to output DICOM file')
    parser.add_argument('-g', '--gantry_angle', type=str, default=90.0,
                        help='Gantry angle [degrees]. ')
    parser.add_argument('-tp', '--table_position', type=str, default="0.0,0.0,0.0",
                        help='New table position vertical,longitudinal,lateral [cm].')
    parser.add_argument('-sp', '--snout_position', type=float, default="42.1",
                        help='Set new snout position [cm]')
    parser.add_argument('-tm', '--treatment_machine', type=str, default="tr4",
                        help='Treatment Machine Name')
    parser.add_argument('-pl', '--plan_label', type=str, default="DefaultLabel",
                        help='Set plan label')
    parser.add_argument('-pn', '--patient_name', type=str, default="DefaultName",
                        help='Set patient name')
    parser.add_argument('-pi', '--patient_id', type=str, default="DefaultID",
                        help='Set patient ID')
    parser.add_argument('-rn', '--reviewer_name', type=str, default="DefaultReviewer",
                        help='Set reviewer name')
    parser.add_argument('-on', '--operator_name', type=str, default="DefaultOperator",
                        help='Set operator name')
    parser.add_argument('-v', '--verbosity', action='count', default=0,
                        help='Give more output. Option is additive, can be used up to 3 times')
    parser.add_argument('-V', '--version', action='version',
                        version=__version__)
    parser.add_argument('--dose_plot', action='store_true', default=False,
                        help='Generate a dose plot of the plan')
    parser.add_argument('--dose_plot_filepath', type=str, default="plot_dose.png",
                        help='Filepath for dose plot image')
    parser.add_argument('--dose_plot_fwhm', type=str, default=DEFAULT_FWHMS,
                        help=f'FWHM (cm) for dose plot Gaussian kernel, as two values for x and y \
                            (e.g. --dose_plot_fwhm={DEFAULT_FWHMS})')

    # Subparsers for pattern types
    subparsers = parser.add_subparsers(dest="pattern_type", required=True,
                                       help="Specify spot pattern type")

# Square pattern
    square = subparsers.add_parser('square', help='Generate a square spot pattern')
    square.add_argument('dx', type=float, help='Field width x [cm]')
    square.add_argument('dy', type=float, help='Field height y [cm]')
    square.add_argument('--spacing', type=float, default=DEFAULT_SPOT_SPACING,
                        help='Spot spacing [cm]')
    square.add_argument('--mu-per-spot', type=float, default=DEFAULT_MU_PER_SPOT,
                        help='MU per spot')
    square.add_argument('--energy', type=float, default=DEFAULT_ENERGY,
                        help='Beam energy [MeV]')
    square.add_argument('--hex', action='store_true', default=False,
                        help='Use hexagonal pattern instead of square')
    # add x y offsets
    square.add_argument('--xoffset', type=float, default=0.0,
                        help='X offset [cm]')
    square.add_argument('--yoffset', type=float, default=0.0,
                        help='Y offset [cm]')
    square.add_argument('--trim_corners', action='store_true', default=False,
                        help='Trim corners of square pattern.')
    square.add_argument('--boost_rim', type=float, default=1.0,
                        help='Boost rim spots by multiplying their MU by this factor.')

    # Circle pattern
    circle = subparsers.add_parser('circle', help='Generate a circular spot pattern')
    circle.add_argument('diameter', type=float, help='Field diameter [cm]')
    circle.add_argument('--spacing', type=float, default=DEFAULT_SPOT_SPACING,
                        help='Spot spacing [cm]')
    circle.add_argument('--mu-per-spot', type=float, default=DEFAULT_MU_PER_SPOT,
                        help='MU per spot')
    circle.add_argument('--energy', type=float, default=DEFAULT_ENERGY,
                        help='Beam energy [MeV]')
    circle.add_argument('--xoffset', type=float, default=0.0,
                        help='X offset [cm]')
    circle.add_argument('--yoffset', type=float, default=0.0,
                        help='Y offset [cm]')
    circle.add_argument('--boost_rim', type=float, default=1.0,
                        help='Boost rim spots by multiplying their MU by this factor.')

    # Image pattern
    image = subparsers.add_parser('image', help='Generate a spot pattern from image')
    image.add_argument('width', type=float, help='Field width [cm]')
    image.add_argument('height', type=float, help='Field height [cm]')
    image.add_argument('image_path', type=str, help='Path to image file')
    image.add_argument('--mu-per-spot', type=float, default=DEFAULT_MU_PER_SPOT,
                       help='Average amount of MU per spot')

    image.add_argument('--energy', type=float, default=DEFAULT_ENERGY,
                       help='Beam energy [MeV]')
    image.add_argument('--spacing', type=float, default=DEFAULT_SPOT_SPACING,
                       help='Spot spacing [cm]')
    image.add_argument('--threshold', type=float, default=0.5,
                       metavar='THRESHOLD', choices=[0.0, 1.0],
                       help='Threshold (0–1) for spot activation from image')
    # add x y offsets
    image.add_argument('--xoffset', type=float, default=0.0,
                       help='X offset [cm]')
    image.add_argument('--yoffset', type=float, default=0.0,
                       help='Y offset [cm]')

    return parser.parse_args(args)


def get_model_from_args(args) -> PlanInputModel:
    """
    Return a populated PlanInputModel from the command line arguments.
    """
    model = PlanInputModel(
        plan_id=args.output,
        plan_name=args.plan_label,
        plan_description="Generated by dicomplan"
    )

    # Set the output path
    model.output_path = args.output

    # Set the treatment machine
    model.field_treatment_machine = args.treatment_machine

    # Set the gantry angles
    if args.gantry_angle is not None:
        model.field_gantry_angle = args.gantry_angle

    if args.table_position is not None:
        parts = [float(pos) for pos in args.table_position.split(',')]
        model.field_table_position = [parts[0], parts[1], parts[2]]

    # Set the snout position
    model.field_snout_position = args.snout_position

    # Set the plan label
    model.plan_label = args.plan_label

    # Set the patient name and ID
    model.plan_patient_name = args.patient_name
    model.plan_patient_id = args.patient_id

    # Set the reviewer and operator names
    model.plan_reviewer_name = args.reviewer_name
    model.plan_operator_name = args.operator_name

    # Set the spot spacing and MU per spot
    model.spot_spacing = args.spacing
    model.spot_mu = args.mu_per_spot

    # set plotting options
    model.plot_dose = args.dose_plot
    model.plot_dose_filepath = args.dose_plot_filepath
    model.plot_dose_fwhm = [float(fwhm) for fwhm in args.dose_plot_fwhm.split(',')]

    # Set the energy
    if args.energy is not None:
        model.spot_energy = args.energy

    if getattr(args, 'boost_rim', 1.0) > 1.0:
        model.boost_rim = args.boost_rim

    # Set the pattern type and parameters based on subparser choice
    if args.pattern_type == 'square':
        model.spot_shape = 'square'
        model.spot_xymin = [-args.dx / 2, -args.dy / 2]
        model.spot_xymax = [args.dx / 2, args.dy / 2]
        model.trim_corners = args.trim_corners
        if args.hex:
            model.spot_pattern_type = 'hexagonal'
        else:
            model.spot_pattern_type = 'square'

    elif args.pattern_type == 'circle':
        model.spot_shape = 'circle'
        model.spot_diameter = args.diameter
        model.spot_center = [0.0, 0.0]

    elif args.pattern_type == 'image':
        model.spot_shape = 'image'
        model.spot_image_path = args.image_path
        model.spot_xymin = [-args.width / 2, -args.height / 2]
        model.spot_xymax = [args.width / 2, args.height / 2]

    _apply_offset(model, args.xoffset, args.yoffset)

    return model


def _apply_offset(model: PlanInputModel, xoffset: float, yoffset: float) -> None:
    """
    Apply the offset to the model.
    """

    if model.spot_shape == 'circle':
        model.spot_center[0] += xoffset
        model.spot_center[1] += yoffset
    else:   # square or image
        model.spot_xymin[0] += xoffset
        model.spot_xymax[0] += xoffset
        model.spot_xymin[1] += yoffset
        model.spot_xymax[1] += yoffset
