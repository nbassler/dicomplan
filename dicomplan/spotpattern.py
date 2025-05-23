import numpy as np
from dicomplan.model import PlanInputModel


def generate_spot_pattern(model: PlanInputModel) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a spot pattern based on the provided model.
    """
    if model.spot_shape == 'square':
        return generate_square_pattern(model)
    elif model.spot_shape == 'circular':
        return generate_circular_pattern(model)
    elif model.spot_shape == 'image':
        return generate_image_pattern(model)
    else:
        raise ValueError(f"Unknown spot shape: {model.spot_shape}")


def generate_square_pattern(model: PlanInputModel) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a square spot pattern.
    """

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

        # Create a grid of spots
        x_coords = np.linspace(model.spot_xymin[0], model.spot_xymax[0], num_spots_x)
        y_coords = np.linspace(model.spot_xymin[1], model.spot_xymax[1], num_spots_y)

    return np.meshgrid(x_coords, y_coords)


def generate_circular_pattern(model: PlanInputModel) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a circular spot pattern.
    """
    # Create a grid of points
    theta = np.linspace(0, 2 * np.pi, model.spot_count)
    r = model.spot_diameter / 2

    x_coords = r * np.cos(theta) + model.spot_center[0]
    y_coords = r * np.sin(theta) + model.spot_center[1]

    return x_coords, y_coords


def generate_image_pattern(model: PlanInputModel) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a spot pattern based on an image.
    """
    # Load the image and convert it to a binary mask
    image = np.load(model.spot_image_path)
    mask = image > 0  # Assuming non-zero values are part of the pattern

    # Get the coordinates of the spots
    y_coords, x_coords = np.where(mask)

    # Scale the coordinates to the desired spacing
    x_coords = x_coords * model.spot_spacing
    y_coords = y_coords * model.spot_spacing

    return x_coords, y_coords
