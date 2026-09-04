import csv
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from dicomplan.model import PlanInputModel
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


@dataclass
class SpotLayer:
    """
    One energy layer of a plan: every spot delivered at a single nominal beam energy.

    A plan built from one of the geometric patterns has exactly one layer. A CSV spot
    list with an energy column has one layer per energy, in ascending energy order.
    """
    energy: float          # MeV
    coords: np.ndarray     # flat [x0, y0, x1, y1, ...] in cm
    weights: np.ndarray    # per-spot weight, absolute MU when the model says so

    @property
    def nspots(self) -> int:
        return len(self.coords) // 2


def _flatten_layers(layers: list[SpotLayer]) -> tuple[np.ndarray, np.ndarray]:
    """Concatenate the layers into the flat (coords, weights) pair of a single-layer plan."""
    coords = np.concatenate([layer.coords for layer in layers])
    weights = np.concatenate([layer.weights for layer in layers])
    return coords, weights


def generate_spot_layers(model: PlanInputModel) -> list[SpotLayer]:
    """
    Generate the energy layers of the plan described by the model.

    This is the entry point used to build the DICOM control points: every layer becomes
    one pair of them. Only CSV spot lists can produce more than one layer; the geometric
    patterns all return a single layer at model.spot_energy.

    The dose plot, if requested, is drawn once over all layers combined.
    """
    if model.spot_shape == 'csv':
        layers = generate_csv_layers(model)
    else:
        layers = [SpotLayer(model.spot_energy, *generate_spot_pattern(model))]

    logger.info("number of energy layers: %d", len(layers))

    if model.plot_dose:
        logger.info(f"Generating dose plot {model.plot_dose_filepath} with FWHM {model.plot_dose_fwhm} cm")
        coords, weights = _flatten_layers(layers)
        _dose_plot(model.plot_dose_filepath, model, coords, weights, model.plot_dose_fwhm)

    return layers


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
        coords, weights = generate_square_pattern(model)
    elif model.spot_shape == 'circle':
        coords, weights = generate_circular_pattern(model)
    elif model.spot_shape == 'image':
        coords, weights = generate_image_pattern(model)
    elif model.spot_shape == 'csv':
        coords, weights = generate_csv_pattern(model)
    else:
        raise ValueError(f"Unknown spot shape: {model.spot_shape}")

    return coords, weights


def generate_square_pattern(model: PlanInputModel) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a square spot pattern in
    [x0, y0, x0, y1, ..., x0, yn,
     x1, y0, ..., x1, yn,
     ...
     xn, y0, ..., xn, yn] format.
    """

    logger.debug("Generating square pattern with spot spacing %s cm", model.spot_spacing)

    if model.spot_xymin is None or model.spot_xymax is None:
        raise ValueError("spot_xymin and spot_xymax must be defined for square pattern")
    if model.spot_spacing is None:
        raise ValueError("spot_spacing must be defined for square pattern")

    # Extract to locals - Pylance now knows these are list[float] and float
    xymin = model.spot_xymin
    xymax = model.spot_xymax
    spacing = model.spot_spacing

    if model.spot_pattern_type == 'hexagonal':
        center_x = (xymin[0] + xymax[0]) / 2
        center_y = (xymin[1] + xymax[1]) / 2
        row_spacing = spacing * np.sqrt(3) / 2  # equidistant nearest neighbours

        # Row indices centred on 0 so the pattern is symmetric around center_y; +1 guards against float truncation
        n_rows = int((xymax[1] - xymin[1]) / 2 / row_spacing) + 1
        row_indices = np.arange(-n_rows, n_rows + 1)

        # Column indices centred on 0; +1 ensures boundary spots aren't missed due to float truncation
        n_cols = int((xymax[0] - xymin[0]) / 2 / spacing) + 1

        eps = spacing * 1e-6  # float tolerance for boundary inclusion
        all_x = []
        all_y = []
        for k in row_indices:
            yi = center_y + k * row_spacing
            if yi < xymin[1] - eps or yi > xymax[1] + eps:  # clip rows outside y bounds
                continue
            if k % 2 == 0:
                row_x = center_x + np.arange(-n_cols, n_cols + 1) * spacing
            else:
                row_x = center_x + (np.arange(-n_cols, n_cols + 1) + 0.5) * spacing
            # clip to x bounding box
            row_x = row_x[(row_x >= xymin[0] - eps) & (row_x <= xymax[0] + eps)]
            all_x.append(row_x)
            all_y.append(np.full_like(row_x, yi))

        x_coords = np.concatenate(all_x)
        y_coords = np.concatenate(all_y)
        coords = np.column_stack((x_coords, y_coords)).ravel()
    else:

        # Calculate the number of spots in each direction
        num_spots_x = int((xymax[0] - xymin[0]) / spacing)
        num_spots_y = int((xymax[1] - xymin[1]) / spacing)

        logger.debug("Number of spots in x direction: %d", num_spots_x)
        logger.debug("Number of spots in y direction: %d", num_spots_y)

        # Create a grid of spots
        if spacing > 0:
            # Use arange to ensure we cover the entire range with the specified spacing
            # This ensures that the last spot is included if it fits within the bounds
            x_coords = np.arange(xymin[0],
                                 xymax[0] + spacing * 0.5,
                                 spacing)
            y_coords = np.arange(xymin[1],
                                 xymax[1] + spacing * 0.5,
                                 spacing)
        else:
            # alternatively,
            # if now spot spacing was given, we can use linspace to ensure we cover the entire range
            # but then the spot spacing is changed so the corners always align with the requested rectangle
            x_coords = np.linspace(xymin[0], xymax[0], num_spots_x)
            y_coords = np.linspace(xymin[1], xymax[1], num_spots_y)

        coords = _flat_grid(x_coords, y_coords)
    assert len(coords) % 2 == 0, "Coordinate list must contain pairs (x, y)"
    nspots = len(coords) // 2
    weights = np.ones(nspots, dtype=np.float32)

    # If trim_corners is True, we need to remove the spots that are in the corners of the square
    if model.trim_corners:
        logger.debug("Trimming corners of square pattern")
        cx: np.ndarray = coords[0::2]
        cy: np.ndarray = coords[1::2]
        mask = ~((cx < xymin[0] + spacing) &
                 (cy < xymin[1] + spacing) |
                 (cx > xymax[0] - spacing) &
                 (cy < xymin[1] + spacing) |
                 (cx < xymin[0] + spacing) &
                 (cy > xymax[1] - spacing) |
                 (cx > xymax[0] - spacing) &
                 (cy > xymax[1] - spacing))
        coords = np.column_stack((cx, cy)).ravel()[mask.repeat(2)]
        weights = weights[mask]

    if model.boost_rim > 1.0:
        logger.debug("Boosting rim spots by factor %s", model.boost_rim)
        weights = _boost_rim_spots(coords, weights, model)

    return coords, weights


def generate_circular_pattern(model: PlanInputModel) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a circular spot pattern on a Cartesian mesh, with uniform spacing.
    Only spots inside the circle defined by model.spot_diameter and model.spot_center are kept.
    """

    if model.spot_diameter is None:
        raise ValueError("spot_diameter must be defined for circular pattern")
    if model.spot_center is None:
        raise ValueError("spot_center must be defined for circular pattern")
    if model.spot_spacing is None:
        raise ValueError("spot_spacing must be defined for circular pattern")

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

    if model.boost_rim > 1.0:
        logger.debug("Boosting rim spots by factor %s", model.boost_rim)
        weights = _boost_rim_spots(coords, weights, model)

    return coords, weights


def generate_image_pattern(model: PlanInputModel) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a spot pattern based on an image.
    """
    from PIL import Image

    if model.spot_image_path is None:
        raise ValueError("spot_image_path must be defined for image pattern")
    if model.spot_xymin is None or model.spot_xymax is None:
        raise ValueError("spot_xymin and spot_xymax must be defined for image pattern")
    if model.spot_spacing is None:
        raise ValueError("spot_spacing must be defined for image pattern")

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
    image_resized = image.resize((target_width_px, target_height_px), Image.Resampling.BILINEAR)
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


def _read_csv_spots(path: str) -> tuple[list[float], list[float], list[float], Optional[list[float]]]:
    """
    Read a CSV spot list and return the x, y, mu and (optional) energy columns.

    The x, y and mu columns are mandatory. The energy column is optional; when absent,
    None is returned in its place and the whole spot list forms a single energy layer at
    the energy given on the command line.
    """
    with open(path, newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("CSV file must contain 'x', 'y' and 'mu' columns")

        columns = {name.strip().lower(): name for name in reader.fieldnames}
        missing_columns = {'x', 'y', 'mu'} - set(columns)
        if missing_columns:
            missing = "', '".join(sorted(missing_columns))
            raise ValueError(f"CSV file must contain '{missing}' column(s)")

        has_energy = 'energy' in columns

        x_values: list[float] = []
        y_values: list[float] = []
        mu_values: list[float] = []
        energy_values: list[float] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                x_values.append(float(row[columns['x']]))
                y_values.append(float(row[columns['y']]))
                mu_values.append(float(row[columns['mu']]))
                if has_energy:
                    energy_values.append(float(row[columns['energy']]))
            except (TypeError, ValueError) as exc:
                expected = "x, y, mu and energy" if has_energy else "x, y and mu"
                raise ValueError(f"CSV row {row_number} must contain numeric {expected} values") from exc

    if not x_values:
        raise ValueError("CSV file must contain at least one spot")

    return x_values, y_values, mu_values, energy_values if has_energy else None


def _split_energy_layers(energies: list[float]) -> list[tuple[int, int]]:
    """
    Split a per-spot energy column into layers of consecutive spots sharing one energy.

    Returns a list of (start, stop) row index pairs. Every change of energy from one row
    to the next starts a new layer, so the layer order is the row order of the file.

    Energy must increase strictly from layer to layer. A repeated energy further down the
    file therefore fails rather than silently producing two layers at the same energy,
    which also catches a spot list that was never sorted by energy in the first place.
    """
    bounds = []
    start = 0
    for row in range(1, len(energies) + 1):
        if row == len(energies) or energies[row] != energies[row - 1]:
            bounds.append((start, row))
            start = row

    for (prev_start, _), (this_start, _) in zip(bounds, bounds[1:]):
        previous, current = energies[prev_start], energies[this_start]
        if current <= previous:
            raise ValueError(
                f"CSV energy layers must be in ascending energy order, but the layer starting "
                f"on row {this_start + 2} has energy {current} MeV after {previous} MeV. "
                f"Sort the spot list by ascending energy."
            )

    return bounds


def generate_csv_layers(model: PlanInputModel) -> list[SpotLayer]:
    """
    Generate the energy layers of a spot pattern from a CSV file.

    The CSV file must have x, y and mu columns and may have an energy column. Coordinates
    are in cm, mu is the absolute per-spot monitor unit value and energy is in MeV. Every
    change of the energy column starts a new energy layer; without an energy column the
    whole file is one layer at model.spot_energy.
    """
    if model.spot_csv_path is None:
        raise ValueError("spot_csv_path must be defined for csv pattern")

    x_values, y_values, mu_values, energies = _read_csv_spots(model.spot_csv_path)

    xoffset, yoffset = model.spot_offset
    x_coords = np.asarray(x_values) + xoffset
    y_coords = np.asarray(y_values) + yoffset
    coords = np.column_stack((x_coords, y_coords))
    weights = np.asarray(mu_values, dtype=np.float32)

    if energies is None:
        return [SpotLayer(model.spot_energy, coords.ravel(), weights)]

    bounds = _split_energy_layers(energies)
    logger.debug("CSV spot list split into %d energy layers", len(bounds))
    return [SpotLayer(energies[start], coords[start:stop].ravel(), weights[start:stop])
            for start, stop in bounds]


def generate_csv_pattern(model: PlanInputModel) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a spot pattern based on a CSV file, with all energy layers concatenated.

    Use generate_csv_layers() where the per-layer split matters; this flat view is what
    the single-energy patterns return and is what the dose plot works on.
    """
    return _flatten_layers(generate_csv_layers(model))


def _flat_grid(x_coords: np.ndarray, y_coords: np.ndarray) -> np.ndarray:
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


def _boost_rim_spots(coords: np.ndarray, weights: np.ndarray, model: PlanInputModel) -> np.ndarray:
    """
    Boost the weights of rim spots by multiplying them by the given factor.
    Rim spots are the outermost spots of the pattern: the leftmost and rightmost x-columns,
    and the top/bottom spot of every x-column.
    """

    logger.info("Boosting rim spots by factor %s", model.boost_rim)

    x_coords = coords[0::2]
    y_coords = coords[1::2]
    atol = (np.max(x_coords) - np.min(x_coords)) * 1e-6

    unique_x = np.unique(x_coords)
    x_min, x_max = unique_x[0], unique_x[-1]

    rim_mask = np.zeros(len(weights), dtype=bool)

    for x in unique_x:
        col_mask = np.abs(x_coords - x) < atol
        y_at_x = y_coords[col_mask]
        if len(y_at_x) == 0:
            continue
        # outermost x-columns: all spots are rim spots
        if np.abs(x - x_min) < atol or np.abs(x - x_max) < atol:
            rim_mask |= col_mask
        else:
            # interior columns: only top and bottom spots
            y_min, y_max = np.min(y_at_x), np.max(y_at_x)
            rim_mask |= col_mask & ((np.abs(y_coords - y_min) < atol) | (np.abs(y_coords - y_max) < atol))

    weights[rim_mask] *= model.boost_rim
    return weights


def _dose_plot_extent(coords: np.ndarray, margin: float = 1.0) -> tuple[float, float, float, float]:
    """
    Return the (xmin, xmax, ymin, ymax) window in cm covering all spots plus a margin.

    The extent is derived from the actual spot positions rather than from
    model.spot_xymin/spot_xymax, which are only meaningful for the square and image
    patterns and stay at the origin for csv spot lists - clipping every spot outside
    the margin out of the plot.
    """
    spot_xy = coords.reshape(-1, 2)
    xmin, ymin = spot_xy.min(axis=0)
    xmax, ymax = spot_xy.max(axis=0)
    return float(xmin - margin), float(xmax + margin), float(ymin - margin), float(ymax + margin)


def _dose_plot(fname: str, model: PlanInputModel, coords: np.ndarray, weights: np.ndarray, fwhm: list[float]) -> None:
    '''
    Generate a dose plot of the plan, and save it as a PNG file.
    The dose is calculated as a sum of Gaussian functions centered at each spot, with the given
    full width at half maximum (FWHM).
    '''

    resolution = 0.01  # cm
    xmin, xmax, ymin, ymax = _dose_plot_extent(coords)
    x = np.arange(xmin, xmax, resolution)
    y = np.arange(ymin, ymax, resolution)
    X, Y = np.meshgrid(x, y, indexing='ij')
    dose = np.zeros_like(X)

    sx2 = fwhm[0]**2 / (4 * np.log(2))
    sy2 = fwhm[1]**2 / (4 * np.log(2))

    for (x0, y0), w in zip(coords.reshape(-1, 2), weights):
        dose += w * np.exp(-(((X - x0)**2 / sx2) + ((Y - y0)**2 / sy2)))
    # Normalize dose for visualization
    dose /= np.max(dose)
    plt.figure(figsize=(6, 5))
    # use crazy discrete color map to better visualize the dose distribution
    mycmap = plt.get_cmap('tab20', 20)  # 20 discrete colors for 5% variations in dose
    plt.imshow(dose.T, extent=(x[0], x[-1], y[0], y[-1]), origin='lower', cmap=mycmap)
    plt.colorbar(label='Relative Dose')
    plt.title(f'Dose Distribution {model.output_path}')
    plt.xlabel('X (cm)')
    plt.ylabel('Y (cm)')
    # add grid lines: 1 cm major, 0.5 cm minor
    ax = plt.gca()
    from matplotlib.ticker import MultipleLocator
    ax.xaxis.set_major_locator(MultipleLocator(1.0))
    ax.yaxis.set_major_locator(MultipleLocator(1.0))
    ax.xaxis.set_minor_locator(MultipleLocator(0.5))
    ax.yaxis.set_minor_locator(MultipleLocator(0.5))
    ax.grid(True, which='major', color='black', linestyle='-', linewidth=0.5)
    ax.grid(True, which='minor', color='gray', linestyle='--', linewidth=0.25)

    plt.savefig(fname)
    plt.close()
