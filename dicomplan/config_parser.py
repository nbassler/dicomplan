import argparse
from dicomplan.__version__ import __version__


def parse_arguments(args=None):
    """
    """
    parser = argparse.ArgumentParser(
        description='Create simple ECLIPSE DICOM proton therapy treatment plans.')

    parser.add_argument('-o', '--output', default="output.dcm",
                        help='Path to output DICOM file')
    parser.add_argument('-g', '--gantry_angles', type=str, default=None,
                        help='List of comma-separated gantry angles')
    parser.add_argument('-tp', '--table_position', type=str, default=None,
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

    return parser.parse_args(args)
