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

    # Configure root logger at WARNING so third-party libraries (matplotlib etc.) stay quiet.
    # Verbosity flags only raise the level for our own package logger.
    logging.basicConfig(level=logging.WARNING)
    if parsed_args.verbosity == 1:
        logging.getLogger('dicomplan').setLevel(logging.INFO)
    elif parsed_args.verbosity > 1:
        logging.getLogger('dicomplan').setLevel(logging.DEBUG)

    d = Dicom()
    d.apply_model(m)

    if m.output_path is None:
        logger.error("Output path is not set. Cannot write DICOM file.")
        return 1
    d.write(m.output_path)

    logger.info(f"Plan written to {m.output_path}")


if __name__ == '__main__':
    sys.exit(main())
