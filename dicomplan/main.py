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

    # Root logger stays at WARNING so third-party libraries (matplotlib etc.) stay quiet.
    logging.basicConfig(level=logging.WARNING)

    # Give the dicomplan logger its own handler and disable propagation so its records
    # never reach the root handler's WARNING gate, allowing -v/-vv to work correctly.
    pkg_logger = logging.getLogger('dicomplan')
    pkg_handler = logging.StreamHandler()
    pkg_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
    pkg_logger.addHandler(pkg_handler)
    pkg_logger.propagate = False
    if parsed_args.verbosity == 1:
        pkg_logger.setLevel(logging.INFO)
    elif parsed_args.verbosity > 1:
        pkg_logger.setLevel(logging.DEBUG)
    else:
        pkg_logger.setLevel(logging.WARNING)

    d = Dicom()
    d.apply_model(m)

    if m.output_path is None:
        logger.error("Output path is not set. Cannot write DICOM file.")
        return 1
    d.write(m.output_path)

    logger.info(f"Plan written to {m.output_path}")


if __name__ == '__main__':
    sys.exit(main())
