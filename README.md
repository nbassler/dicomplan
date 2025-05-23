# dicomplan
Tool for making simple proton plans.

# usage examples

```
PYTHONPATH=. python3 dicomplan/main.py -vv -o test3.dcm square 1 2 --energy 70 --spacing 0.4 --mu-per-spot=40
PYTHONPATH=. python3 dicomplan/main.py -vv -o test4.dcm circle 5  --energy 120 --spacing 0.4 --mu-per-spot=40
PYTHONPATH=. python3 dicomplan/main.py -vv -o test2.dcm image 10 15 res/img2.png --spacing 0.4 --mu-per-spot=30 --energy 200
```
use -h option for more info.


```
usage: main.py [-h] [-o OUTPUT] [-g GANTRY_ANGLE] [-tp TABLE_POSITION] [-sp SNOUT_POSITION] [-tm TREATMENT_MACHINE] [-pl PLAN_LABEL]
               [-pn PATIENT_NAME] [-pi PATIENT_ID] [-rn REVIEWER_NAME] [-on OPERATOR_NAME] [-v] [-V]
               {square,circle,image} ...

Create simple ECLIPSE DICOM proton therapy treatment plans.

positional arguments:
  {square,circle,image}
                        Specify spot pattern type
    square              Generate a square spot pattern
    circle              Generate a circular spot pattern
    image               Generate a spot pattern from image

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Path to output DICOM file
  -g GANTRY_ANGLE, --gantry_angle GANTRY_ANGLE
                        Gantry angle [degrees].
  -tp TABLE_POSITION, --table_position TABLE_POSITION
                        New table position vertical,longitudinal,lateral [cm]. Negative values should be in quotes and leading space.
  -sp SNOUT_POSITION, --snout_position SNOUT_POSITION
                        Set new snout position [cm]
  -tm TREATMENT_MACHINE, --treatment_machine TREATMENT_MACHINE
                        Treatment Machine Name
  -pl PLAN_LABEL, --plan_label PLAN_LABEL
                        Set plan label
  -pn PATIENT_NAME, --patient_name PATIENT_NAME
                        Set patient name
  -pi PATIENT_ID, --patient_id PATIENT_ID
                        Set patient ID
  -rn REVIEWER_NAME, --reviewer_name REVIEWER_NAME
                        Set reviewer name
  -on OPERATOR_NAME, --operator_name OPERATOR_NAME
                        Set operator name
  -v, --verbosity       Give more output. Option is additive, can be used up to 3 times
  -V, --version         show program's version number and exit
```

subcommands, e.g.
```
usage: main.py square [-h] [--spacing SPACING] [--mu-per-spot MU_PER_SPOT] [--energy ENERGY] [--hex] [--xoffset XOFFSET] [--yoffset YOFFSET]
                      width height

positional arguments:
  width                 Field width [cm]
  height                Field height [cm]

options:
  -h, --help            show this help message and exit
  --spacing SPACING     Spot spacing [cm]
  --mu-per-spot MU_PER_SPOT
                        MU per spot
  --energy ENERGY       Beam energy [MeV]
  --hex                 Use hexagonal pattern instead of square
  --xoffset XOFFSET     X offset [cm]
  --yoffset YOFFSET     Y offset [cm]
```