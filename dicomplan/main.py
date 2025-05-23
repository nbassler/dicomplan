from dicomplan.config_parser import parse_arguments
from dicomplan.config_parser import get_model_from_args

from dicomplan.dicom import Dicom

import sys
import logging

logger = logging.getLogger(__name__)


def main(args=None):
    """
    """
    if args is None:
        args = sys.argv[1:]

    # Parse the command-line arguments
    parsed_args = parse_arguments(args)
    # Populate the model from the parsed arguments
    m = get_model_from_args(parsed_args)

    # Set up logging based on verbosity
    if parsed_args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    elif parsed_args.verbosity > 1:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig()

    print(parsed_args.reviewer_name)

    d = Dicom()
    d.apply_model(m)
    d.write(m.output_path)


if __name__ == '__main__':
    sys.exit(main())
