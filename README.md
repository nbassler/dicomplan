# dicomplan

[![CI](https://github.com/nbassler/dicomplan/actions/workflows/ci.yml/badge.svg)](https://github.com/nbassler/dicomplan/actions/workflows/ci.yml)
[![Lint](https://github.com/nbassler/dicomplan/actions/workflows/lint.yml/badge.svg)](https://github.com/nbassler/dicomplan/actions/workflows/lint.yml)
[![CodeQL](https://github.com/nbassler/dicomplan/actions/workflows/codeql.yml/badge.svg)](https://github.com/nbassler/dicomplan/actions/workflows/codeql.yml)

Command-line tool for generating simple proton therapy DICOM RT Ion plans compatible with Varian ECLIPSE.
Useful for creating phantom plans, test plans, and commissioning fields with square, circular, or image-based spot patterns.

## Installation

```bash
pip install git+https://github.com/nbassler/dicomplan.git
```

## Usage

```
dicomplan [options] {square,circle,image,csv} ...
```

### Spot pattern types

| Subcommand | Positional args | Description |
|------------|-----------------|-------------|
| `square` | `dx dy` | Rectangular field, `dx` × `dy` cm |
| `circle` | `diameter` | Circular field with given diameter in cm |
| `image` | `width height file.png` | Field shaped by a grayscale PNG image |
| `csv` | `file.csv` | Field described by a CSV spot list with `x`, `y` [cm] and `mu` [MU] columns |

### Global options

| Option | Default | Description |
|--------|---------|-------------|
| `-o FILE` | `output.dcm` | Output DICOM file |
| `-g ANGLE` | `90.0` | Gantry angle [degrees] |
| `-sp CM` | `42.1` | Snout position [cm] |
| `-tp V,L,LAT` | `0,0,0` | Table position vertical,longitudinal,lateral [cm] |
| `-tm NAME` | `tr4` | Treatment machine name |
| `-pl LABEL` | `DefaultLabel` | Plan label |
| `-pn NAME` | `DefaultName` | Patient name |
| `-pi ID` | `DefaultID` | Patient ID |
| `-rn NAME` | `DefaultReviewer` | Reviewer name |
| `-on NAME` | `DefaultOperator` | Operator name |
| `--dose_plot` | off | Generate a dose distribution plot |
| `--dose_plot_filepath FILE` | `plot_dose.png` | Output path for dose plot |
| `--dose_plot_fwhm X,Y` | `1.000,1.000` | Gaussian FWHM [cm] for dose plot (x,y) |
| `-v` / `-vv` | off | Verbose / debug output |
| `-V` | — | Show version and exit |

### Subcommand options

| Option | Default | `square` | `circle` | `image` | `csv` | Description |
|--------|---------|:--------:|:--------:|:-------:|:-----:|-------------|
| `--spacing CM` | `0.5` | ✓ | ✓ | ✓ | | Spot spacing [cm] |
| `--mu-per-spot MU` | `10.0` | ✓ | ✓ | ✓ | | MU per spot |
| `--energy MEV` | `120.0` | ✓ | ✓ | ✓ | ✓ | Beam energy [MeV] |
| `--xoffset CM` | `0.0` | ✓ | ✓ | ✓ | ✓ | X offset [cm] |
| `--yoffset CM` | `0.0` | ✓ | ✓ | ✓ | ✓ | Y offset [cm] |
| `--boost_rim FACTOR` | `1.0` | ✓ | ✓ | | | Multiply rim spot MU by this factor |
| `--hex` | off | ✓ | | | | Use hexagonal spot grid instead of square |
| `--trim_corners` | off | ✓ | | | | Remove corner spots from square pattern |
| `--threshold 0–1` | — | | | ✓ | | Minimum normalised pixel intensity to place a spot |

The `csv` subcommand takes its spot positions and MU from the file, so `--spacing`,
`--mu-per-spot` and `--boost_rim` do not apply to it and are rejected.

Run `dicomplan -h` or `dicomplan square -h` for the full option list.

## Examples

Square field, 10 × 10 cm, 70 MeV, 0.4 cm spacing:
```bash
dicomplan -o square.dcm square 10 10 --energy 70 --spacing 0.4 --mu-per-spot 40
```

Circular field, 5 cm diameter, with boosted rim (2×):
```bash
dicomplan -o circle.dcm circle 5 --energy 120 --spacing 0.4 --mu-per-spot 40 --boost_rim 2.0
```

Image-based pattern from a PNG, 10 × 15 cm canvas:
```bash
dicomplan -o image.dcm image 10 15 res/img2.png --spacing 0.4 --mu-per-spot 30 --energy 200
```

Hexagonal grid with custom gantry angle and snout position:
```bash
dicomplan -o hex.dcm -g 270 -sp 30.0 square 8 8 --hex --spacing 0.5 --mu-per-spot 20
```

Generate a dose preview plot alongside the DICOM file:
```bash
dicomplan -o plan.dcm square 10 10 --energy 120 --mu-per-spot 20 --dose_plot
```

Use a CSV spot list with pre-defined (x, y) spots and per-spot MU. The file needs
`x`, `y` and `mu` columns, where the positions are in cm at isocentre and `mu` is the
absolute number of monitor units for that spot (it is not scaled by `--mu-per-spot`):
```csv
x,y,mu
-3.0,-3.0,10.0
3.0,3.0,10.0
0.0,0.0,5.0
```
```bash
dicomplan -o plan.dcm csv spotlist.csv --energy 120
```
`--xoffset` / `--yoffset` shift the whole spot list, and `--dose_plot` works as it does
for the other patterns.

## License

MIT
