import logging
import numpy as np
from dicomplan.model import PlanInputModel

logger = logging.getLogger(__name__)


def generate_spot_pattern(model: PlanInputModel) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a spot pattern based on the provided model.
    Spots are returned as a flat array of x and y coordinates:
    Generate a square spot pattern in
    [x0, y0, x0, y1, ..., x0, yn,
     x1, y0, ..., x1, yn,
     ...
     xn, y0, ..., xn, yn] format.
    The pattern is determined by the spot_shape and spot_pattern_type attributes of the model.
    The spot_shape can be 'square', 'circular', or 'image'.
    The spot_pattern_type can be 'square' or 'hexagonal'.
    The spot_spacing attribute determines the distance between spots in the pattern.
    The spot_xymin and spot_xymax attributes determine the bounding box of the pattern.
    The spot_diameter attribute determines the diameter of the circular pattern.
    """
    logger.debug("Generating circular pattern with model")
    if model.spot_shape == 'square':
        return generate_square_pattern(model)
    elif model.spot_shape == 'circle':
        return generate_circular_pattern(model)
    elif model.spot_shape == 'image':
        return generate_image_pattern(model)
    else:
        raise ValueError(f"Unknown spot shape: {model.spot_shape}")


def generate_square_pattern(model: PlanInputModel) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a square spot pattern in
    [x0, y0, x0, y1, ..., x0, yn,
     x1, y0, ..., x1, yn,
     ...
     xn, y0, ..., xn, yn] format.
    """

    logger.debug("Generating square pattern with spot spacing %s cm", model.spot_spacing)

    if model.spot_pattern_type == 'hexagonal':
        # in case of hexagonal pattern, we need to calculate the coordinates differently
        # every second line will be shifted by half the spacing
        x_coords = np.arange(model.spot_xymin[0], model.spot_xymax[0], model.spot_spacing)
        y_coords = np.arange(model.spot_xymin[1], model.spot_xymax[1], model.spot_spacing)
        y_coords_shifted = y_coords + model.spot_spacing / 2
        x_coords, y_coords = np.meshgrid(x_coords, y_coords)
        x_coords_shifted, y_coords_shifted = np.meshgrid(x_coords, y_coords_shifted)
        x_coords = np.concatenate((x_coords.flatten(), x_coords_shifted.flatten()))
        y_coords = np.concatenate((y_coords.flatten(), y_coords_shifted.flatten()))
    else:

        # Calculate the number of spots in each direction
        num_spots_x = int((model.spot_xymax[0] - model.spot_xymin[0]) / model.spot_spacing)
        num_spots_y = int((model.spot_xymax[1] - model.spot_xymin[1]) / model.spot_spacing)

        logger.debug("Number of spots in x direction: %d", num_spots_x)
        logger.debug("Number of spots in y direction: %d", num_spots_y)

        # Create a grid of spots
        if model.spot_spacing > 0:
            # Use arange to ensure we cover the entire range with the specified spacing
            # This ensures that the last spot is included if it fits within the bounds
            x_coords = np.arange(model.spot_xymin[0],
                                 model.spot_xymax[0] + model.spot_spacing * 0.5,
                                 model.spot_spacing)
            y_coords = np.arange(model.spot_xymin[1],
                                 model.spot_xymax[1] + model.spot_spacing * 0.5,
                                 model.spot_spacing)
        else:
            # alternatively,
            # if now spot spacing was given, we can use linspace to ensure we cover the entire range
            # but then the spot spacing is changed so the corners always align with the requested rectangle
            x_coords = np.linspace(model.spot_xymin[0], model.spot_xymax[0], num_spots_x)
            y_coords = np.linspace(model.spot_xymin[1], model.spot_xymax[1], num_spots_y)

    coords = _flat_grid(x_coords, y_coords)
    assert len(coords) % 2 == 0, "Coordinate list must contain pairs (x, y)"
    nspots = len(coords) // 2
    weights = np.ones(nspots, dtype=np.float32)

    return coords, weights


def generate_circular_pattern(model: PlanInputModel) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a circular spot pattern on a Cartesian mesh, with uniform spacing.
    Only spots inside the circle defined by model.spot_diameter and model.spot_center are kept.
    """
    radius = model.spot_diameter / 2
    spacing = model.spot_spacing
    cx, cy = model.spot_center

    # Define bounding box limits
    xmin = cx - radius
    xmax = cx + radius
    ymin = cy - radius
    ymax = cy + radius

    # Generate grid
    x = np.arange(xmin, xmax + spacing, spacing)
    y = np.arange(ymin, ymax + spacing, spacing)
    X, Y = np.meshgrid(x, y, indexing='ij')

    # Flatten and mask
    dx = X - cx
    dy = Y - cy
    inside = dx**2 + dy**2 <= radius**2

    X_flat = X[inside]
    Y_flat = Y[inside]

    coords = np.column_stack((X_flat, Y_flat)).ravel()
    assert len(coords) % 2 == 0, "Coordinate list must contain pairs (x, y)"
    nspots = len(coords) // 2
    weights = np.ones(nspots, dtype=np.float32)
    return coords, weights


def generate_image_pattern(model: PlanInputModel) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a spot pattern based on an image.
    """
    from PIL import Image

    # Load image, convert to grayscale
    image = Image.open(model.spot_image_path).convert("L")  # "L" = 8-bit grayscale
    img_arr = np.array(image)

    orig_height, orig_width = img_arr.shape
    logger.debug(f"Image shape: {orig_height} x {orig_width}")

    # Determine canvas size in cm
    xmin, ymin = model.spot_xymin
    xmax, ymax = model.spot_xymax
    width_cm = xmax - xmin
    height_cm = ymax - ymin

    # Compute how many pixels would fit given the desired spot spacing
    target_width_px = int(np.round(width_cm / model.spot_spacing))
    target_height_px = int(np.round(height_cm / model.spot_spacing))

    logger.debug(f"Target image size: {target_width_px} x {target_height_px}")

    # Resize the image to match the desired resolution
    image_resized = image.resize((target_width_px, target_height_px), Image.BILINEAR)
    img_arr = np.array(image_resized)[::-1, :]

    # Only keep non-zero pixels
    mask = img_arr > 0
    y_coords, x_coords = np.where(mask)

    # Physical coords (in cm)
    x_coords = x_coords * model.spot_spacing + model.spot_xymin[0]
    y_coords = y_coords * model.spot_spacing + model.spot_xymin[1]

    # Get intensity at each spot
    intensities = img_arr[mask].astype(np.float32)
    weights = intensities / 255.0  # Normalize to [0, 1]

    # invert
    weights = 1 - weights
    # brightness contrast
    # weights = np.clip(weights, 0.0, 1.0)

    # clip spots within thredhold bounds
    threshold_lower = 0.01
    threshold_upper = 1.0
    keep_mask = (weights > threshold_lower) & (weights < threshold_upper)
    weights = weights[keep_mask]
    x_coords = x_coords[keep_mask]
    y_coords = y_coords[keep_mask]

    coords = np.column_stack((x_coords, y_coords)).ravel()

    return coords, weights


def _flat_grid(x_coords: np.ndarray, y_coords: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Flatten the grid of coordinates into a single array.
    The coordinates are returned in the format:
    [x0, y0, x0, y1, ..., x0, yn,
     x1, y0, ..., x1, yn,
     ...
     xn, y0, ..., xn, yn]
    """
    # Flatten the coordinates
    X, Y = np.meshgrid(x_coords, y_coords, indexing='ij')
    return np.column_stack((X.ravel(), Y.ravel())).ravel()
