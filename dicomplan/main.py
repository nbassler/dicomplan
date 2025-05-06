from dicomplan.config_parser import parse_arguments
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

    # Set up logging based on verbosity
    if parsed_args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    elif parsed_args.verbosity > 1:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig()

    print(parsed_args.reviewer_name)

    d = Dicom()
    d.write(parsed_args.output)


if __name__ == '__main__':
    sys.exit(main())
