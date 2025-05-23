import argparse
from dicomplan.__version__ import __version__

from dicomplan.model import PlanInputModel

DEFAULT_SPOT_SPACING = 0.5  # cm
DEFAULT_MU_PER_SPOT = 10.0  # MU
DEFAULT_ENERGY = 120.0  # MeV
DEFAULT_FIELD_WIDTH = 10.0  # cm
DEFAULT_FIELD_HEIGHT = 10.0  # cm
DEFAULT_FIELD_DIAMETER = 10.0  # cm


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
                        help='New table position vertical,longitudinal,lateral [cm]. ' +
                             'Negative values should be in quotes and leading space.')
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
                        version=f'dicomfix {__version__}')

    # Subparsers for pattern types
    subparsers = parser.add_subparsers(dest="pattern_type", required=True,
                                       help="Specify spot pattern type")

# Square pattern
    square = subparsers.add_parser('square', help='Generate a square spot pattern')
    square.add_argument('width', type=float, help='Field width [cm]')
    square.add_argument('height', type=float, help='Field height [cm]')
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
    if args.gantry_angle:
        model.field_gantry_angle = args.gantry_angle

    # Set the table position
    if args.table_position:
        model.field_table_position = [float(pos) for pos in args.table_position.split(',')]

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

    # Set the energy
    model.spot_energy = args.energy

    # Set the pattern type and parameters based on subparser choice
    if args.pattern_type == 'square':
        model.spot_shape = 'square'
        model.spot_xymin = [-args.width / 2, -args.height / 2]
        model.spot_xymax = [args.width / 2, args.height / 2]
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
